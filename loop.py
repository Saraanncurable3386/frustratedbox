"""
FrustratedBox voice loop — edge client (all heavy inference on the GPU).

Runs on the Raspberry Pi 5. Audio I/O, VAD, and Pipecat orchestration are
local; STT, LLM, and TTS are all served from the GPU on a local network, over HTTP.

    mic -> Silero VAD -> OpenAISTTService  (speaches     :8000, faster-whisper)
                      -> OpenAILLMService  (llama-server :8091, Llama 3.1 8B)
                      -> OpenAITTSService  (speaches     :8000, Kokoro)
                      -> speaker (ReSpeaker line-out -> TPA3116 amp)

Setup (see README.md):
    # Pi/Debian: sudo apt install portaudio19-dev
    python3 -m venv venv && source venv/bin/activate
    pip install "pipecat-ai[silero,openai,local,kokoro]" pyaudio
    cp config.sample.toml config.toml   # then edit: backend host, audio, GPIO
    python loop.py

Notes:
    - TTS playback goes out the ReSpeaker's line-out so its hardware AEC has
      its reference signal — that's what makes barge-in work near the speaker.
    - VAD params and MicGateProcessor threshold were tuned indoors; re-tune
      outdoors.
"""

import argparse
import asyncio
import contextlib
import math
import struct
import tomllib
from pathlib import Path

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import (
    AudioRawFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
    Frame,
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transports.local.audio import LocalAudioTransport, LocalAudioTransportParams

from pipecat.services.openai.stt import OpenAISTTService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.openai.tts import OpenAITTSService
import pipecat.services.openai.tts as _openai_tts_module

from eyes import EyeController, EyeState

# --------------------------------------------------------------------------
# Configuration — private config.toml (gitignored), template: config.sample.toml
# --------------------------------------------------------------------------
_CONFIG_PATH = Path(__file__).resolve().parent / "config.toml"
if not _CONFIG_PATH.exists():
    raise SystemExit(
        f"Config file not found: {_CONFIG_PATH}\n"
        "Copy config.sample.toml to config.toml and edit it "
        "(backend endpoints, audio device, GPIO pin)."
    )
with _CONFIG_PATH.open("rb") as _f:
    CONFIG = tomllib.load(_f)

LLM_BASE_URL = CONFIG["backend"]["llm_base_url"]
SPEACHES_URL = CONFIG["backend"]["speaches_url"]

LLM_MODEL = CONFIG["models"]["llm"]
STT_MODEL = CONFIG["models"]["stt"]
TTS_MODEL = CONFIG["models"]["tts"]
TTS_VOICE = CONFIG["models"]["tts_voice"]
_openai_tts_module.VALID_VOICES[TTS_VOICE] = TTS_VOICE  # speaches/Kokoro voice not in pipecat's OpenAI allowlist



def _audio_rms(audio_bytes: bytes) -> float:
    count = len(audio_bytes) // 2
    if not count:
        return 0.0
    samples = struct.unpack_from(f"{count}h", audio_bytes)
    return math.sqrt(sum(s * s for s in samples) / count)


class MicGateProcessor(FrameProcessor):
    """
    While the bot is speaking, drops mic audio whose RMS is below the
    threshold. This passes loud human speech (barge-in) while blocking the
    quieter residual echo that survives the ReSpeaker hardware AEC.

    Tune via `interrupt_rms_threshold` in config.toml (16-bit PCM units, 0–32767):
      raise → harder to barge in, less self-interruption
      lower → easier to barge in, more risk of self-interruption
    """

    def __init__(self, threshold: int) -> None:
        super().__init__()
        self._threshold = threshold
        self._bot_speaking = False

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, BotStartedSpeakingFrame):
            self._bot_speaking = True
        elif isinstance(frame, BotStoppedSpeakingFrame):
            self._bot_speaking = False
        if (
            self._bot_speaking
            and isinstance(frame, AudioRawFrame)
            and direction == FrameDirection.DOWNSTREAM
            and _audio_rms(frame.audio) < self._threshold
        ):
            return
        await self.push_frame(frame, direction)


class VolumeProcessor(FrameProcessor):
    """Scales outgoing TTS audio. gain = volume / 10 (0 = mute, 10 = full PCM)."""

    def __init__(self, volume: int) -> None:
        super().__init__()
        self._gain = volume / 10.0

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)
        if isinstance(frame, AudioRawFrame) and self._gain != 1.0:
            count = len(frame.audio) // 2
            samples = struct.unpack_from(f"{count}h", frame.audio)
            frame.audio = struct.pack(
                f"{count}h",
                *(max(-32768, min(32767, int(s * self._gain))) for s in samples),
            )
        await self.push_frame(frame, direction)


class EyeFrameProcessor(FrameProcessor):
    """Drives the eye bulbs: single ON-pulse when the bot finishes speaking, OFF at all other times.

    When the VL53L1X presence sensor is wired in (Phase 2), trigger
    eyes.set_state(EyeState.ON) on presence detection here.
    """

    def __init__(self, eyes: EyeController) -> None:
        super().__init__()
        self._eyes = eyes

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, BotStoppedSpeakingFrame):
            await self._eyes.flash_once()

        await self.push_frame(frame, direction)


async def main():
    parser = argparse.ArgumentParser(description="FrustratedBox voice loop")
    parser.add_argument("--no-eyes", action="store_true", help="Disable eye bulb control")
    parser.add_argument(
        "--personality", default="box.txt", metavar="FILE",
        help="Path to a plain-text personality file (default: box.txt)",
    )
    parser.add_argument(
        "--volume", type=int, default=10, metavar="N",
        help="Software output volume 0–10 (default: 10 = full PCM; use amp knob as primary control)",
    )
    args = parser.parse_args()

    if not 0 <= args.volume <= 10:
        parser.error("--volume must be between 0 and 10")

    personality_path = Path(args.personality)
    if not personality_path.exists():
        parser.error(f"Personality file not found: {personality_path}")
    persona = personality_path.read_text(encoding="utf-8").strip()

    transport = LocalAudioTransport(
        LocalAudioTransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            input_device_index=CONFIG["audio"]["input_device_index"],  # ReSpeaker 4 Mic Array
            # output uses ALSA default → plughw:2,0 (see ~/.asoundrc) for format conversion
        )
    )

    stt = OpenAISTTService(
        base_url=SPEACHES_URL,
        api_key="speaches",                      # any non-empty value
        settings=OpenAISTTService.Settings(model=STT_MODEL),
    )

    llm = OpenAILLMService(
        base_url=LLM_BASE_URL,
        api_key="not-needed",
        model=LLM_MODEL,
    )

    tts = OpenAITTSService(
        api_key="speaches",
        base_url=SPEACHES_URL,
        model=TTS_MODEL,
        voice=TTS_VOICE,
    )

    context = LLMContext(messages=[{"role": "system", "content": persona}])
    context_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            vad_analyzer=SileroVADAnalyzer(
                params=VADParams(**CONFIG["vad"])
            ),
        ),
    )

    eye_ctx = EyeController() if not args.no_eyes else contextlib.nullcontext()
    async with eye_ctx as eyes:
        pipeline_tail = []
        if eyes is not None:
            pipeline_tail = [EyeFrameProcessor(eyes)]

        pipeline = Pipeline([
            transport.input(),
            MicGateProcessor(CONFIG["audio"]["interrupt_rms_threshold"]),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            VolumeProcessor(args.volume),
            transport.output(),
            context_aggregator.assistant(),
            *pipeline_tail,
        ])

        task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,                 # logs per-stage latency — read these
            ),
        )

        await PipelineRunner().run(task)


if __name__ == "__main__":
    asyncio.run(main())
