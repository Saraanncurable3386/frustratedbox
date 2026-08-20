# Glossary

## Voice pipeline

- **STT — Speech-To-Text.** Converts spoken audio into text. Here: faster-whisper `large-v3-turbo` served by speaches on the 4090.
- **TTS — Text-To-Speech.** Converts the LLM's text reply into spoken audio. Here: Kokoro (82M), also served by speaches.
- **LLM — Large Language Model.** Generates the box's replies. Here: Dolphin 3.0 (a Llama 3.1 8B fine-tune) via llama-server.
- **VAD — Voice Activity Detection.** Decides whether incoming audio contains human speech at all (vs. silence/noise). Here: Silero VAD, running locally on the Pi.
- **AEC — Acoustic Echo Cancellation.** Removes the box's own voice (played through the speaker) from what the microphone picks up, so the bot doesn't hear — and respond to — itself. Done in hardware by the ReSpeaker mic array; this is what makes barge-in possible with the mic sitting next to the speaker.
- **Barge-in.** A human interrupting the bot while it's still speaking. Requires AEC plus the volume gate in `MicGateProcessor`.
- **RMS — Root Mean Square.** A measure of average audio loudness over a chunk of samples. `MicGateProcessor` compares each mic frame's RMS against `interrupt_rms_threshold` from `config.toml` (on the 16-bit PCM scale, 0–32767) to tell loud human speech from quiet residual echo.
- **TTFB — Time To First Byte.** Latency until the *first* chunk of a response arrives (not the whole response). The key responsiveness metric for each streamed stage: STT TTFB ~280ms, LLM TTFB ~0.85s.
- **PCM — Pulse-Code Modulation.** Raw uncompressed audio samples; 16-bit PCM means each sample is an integer in −32768…32767. The format flowing through the pipeline and out to the speaker.
- **ToF — Time of Flight.** Distance measurement by timing how long light takes to bounce back. The VL53L1X laser ToF sensor (Phase 2) detects an approaching person up to ~4m. This is still in exploratory phase, I haven't implemented it yet.

## Audio / OS

- **ALSA — Advanced Linux Sound Architecture.** Linux's audio subsystem. The `~/.asoundrc` config routes the default device through ALSA's `plug` layer so the ReSpeaker's native-only S24_3LE format gets converted automatically.
- **S24_3LE.** ALSA sample-format name: Signed 24-bit, packed in 3 bytes, Little-Endian — the only format the ReSpeaker (UAC1.0) supports natively.
- **UAC — USB Audio Class.** The standard USB audio device protocol; the ReSpeaker is UAC1.0 (hence the ALSA card name `ArrayUAC10`).
- **GPIO — General-Purpose Input/Output.** The Pi's programmable pins. The eye relay is on BCM 17; I2C (BCM 2/3) is reserved for the VL53L1X.
- **BCM — Broadcom (pin numbering).** GPIO numbering scheme named after the Pi's Broadcom chip, as opposed to physical header pin numbers.
- **I2C — Inter-Integrated Circuit.** Two-wire serial bus used by sensors like the VL53L1X.

## Backend / GPU

- **CUDA — Compute Unified Device Architecture.** NVIDIA's GPU compute platform. All inference (STT, LLM, TTS) runs on the 4090 via CUDA.
- **VRAM — Video RAM.** The GPU's onboard memory. ~9GB of the 4090's 24GB is used with all models loaded.
- **GGUF — GPT-Generated Unified Format.** llama.cpp's quantized model file format (the `.gguf` LLM file).
- **Q5_K_M.** A llama.cpp quantization level: ~5-bit "K-quant", medium variant — the size/quality trade-off used for the LLM.
- **ONNX — Open Neural Network Exchange.** Portable neural-network model format; the Kokoro TTS model ships as ONNX (fp16).
- **fp16 / float16 — 16-bit floating point.** Half-precision numbers; halves memory and speeds up GPU inference vs. fp32 with negligible quality loss.
- **OpenAI-compliant API.** Speaches and llama-server expose the same HTTP endpoints as OpenAI's cloud (`/v1/audio/transcriptions`, `/v1/chat/completions`, `/v1/audio/speech`), so standard OpenAI client code works against them.

## Hardware / power

- **BOM — Bill of Materials.** The costed parts list in `BOM.md`.
- **LiFePO4 — Lithium Iron Phosphate.** The 12V 20Ah battery chemistry; deep-cycle safe.
- **BMS — Battery Management System.** The battery's protection circuit; TBC, currently the battery cuts power abruptly when empty.
- **NO (relay contact) — Normally Open.** The relay contact that is disconnected until the coil energizes; the eye-bulb branch runs through it so eyes are off by default.
