#!/usr/bin/env python3
"""
FrustratedBox eye-bulb controller. Can be run independently of the main loop.py file,
so that we can test bulbs.

Hardware: two 12V 21W incandescent bulbs in parallel, switched by an active-high
relay module on a Pi 5 GPIO pin (gpiozero + lgpio backend).  The relay NO
contact is wired in the hot leg: battery → 5A slow-blow fuse → relay NO → bulbs
→ ground.  De-energised = bulbs off.

Eye states
----------
OFF       – steady off  (IDLE / no presence)
ON        – steady on   (presence detected, not yet speaking)
LISTENING – 0.1 s on / 1.0 s off  (user is speaking, box listening)
SPEAKING  – 1.0 s on / 1.0 s off  (box speaking)

Standalone usage
----------------
    python eyes.py off
    python eyes.py on
    python eyes.py listening
    python eyes.py speaking

    # hold the state for a custom duration then turn off:
    python eyes.py speaking --secs 10

Library usage
-------------
    from eyes import EyeController, EyeState

    async with EyeController() as eyes:
        await eyes.set_state(EyeState.ON)
        ...
        await eyes.set_state(EyeState.SPEAKING)
"""

import asyncio
import sys
import tomllib
from enum import Enum
from pathlib import Path

# BCM pin number for the relay signal line — set via [gpio] eye_relay_pin in
# config.toml; falls back to 17 when no config file is present (standalone use).
GPIO_PIN = 17
_cfg_path = Path(__file__).resolve().parent / "config.toml"
if _cfg_path.exists():
    with _cfg_path.open("rb") as _f:
        GPIO_PIN = tomllib.load(_f).get("gpio", {}).get("eye_relay_pin", GPIO_PIN)

# ----- blink timing (on_secs, off_secs) per state -----
_BLINK = {
    "LISTENING": (0.1, 1.0),
    "SPEAKING":  (1.0, 1.0),
}

try:
    from gpiozero import OutputDevice
    from gpiozero.pins.lgpio import LGPIOFactory
    _GPIO_OK = True
except ImportError:
    _GPIO_OK = False


class EyeState(Enum):
    OFF       = "off"
    ON        = "on"
    LISTENING = "listening"
    SPEAKING  = "speaking"


class EyeController:
    """Async eye-bulb controller.  Use as an async context manager or call
    close() when done."""

    def __init__(self, pin: int = GPIO_PIN):
        if _GPIO_OK:
            self._relay: OutputDevice | None = OutputDevice(
                pin,
                active_high=True,    # active-high relay module (HIGH = energised = bulbs on)
                initial_value=False, # pin LOW at boot → relay open → bulbs off
                pin_factory=LGPIOFactory(),
            )
        else:
            self._relay = None
        self._state = EyeState.OFF
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def set_state(self, state: EyeState) -> None:
        if state is self._state:
            return
        self._state = state
        await self._cancel_task()

        if state is EyeState.OFF:
            self._set_pin(False)
        elif state is EyeState.ON:
            self._set_pin(True)
        else:
            on_s, off_s = _BLINK[state.name]
            self._task = asyncio.create_task(self._blink(on_s, off_s))

    async def flash_once(self, on_secs: float = 0.3) -> None:
        """Single ON-pulse then back to OFF — fires once after the bot finishes speaking."""
        self._state = EyeState.OFF
        await self._cancel_task()
        self._task = asyncio.create_task(self._do_flash(on_secs))

    def close(self) -> None:
        """Cancel the blink task; call from non-async contexts (e.g. signal handlers).
        Prefer using the async context manager so __aexit__ can await the task."""
        if self._task and not self._task.done():
            self._task.cancel()

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "EyeController":
        return self

    async def __aexit__(self, *_) -> None:
        await self._cancel_task()   # await so relay isn't closed under a live task
        self._set_pin(False)
        if self._relay:
            self._relay.close()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _blink(self, on_s: float, off_s: float) -> None:
        try:
            while True:
                self._set_pin(True)
                await asyncio.sleep(on_s)
                self._set_pin(False)
                await asyncio.sleep(off_s)
        except asyncio.CancelledError:
            raise   # caller (_cancel_task / __aexit__) sets pin off after awaiting

    async def _do_flash(self, on_secs: float) -> None:
        try:
            self._set_pin(True)
            await asyncio.sleep(on_secs)
            self._set_pin(False)
        except asyncio.CancelledError:
            raise

    async def _cancel_task(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    def _set_pin(self, on: bool) -> None:
        if self._relay:
            if on:
                self._relay.on()
            else:
                self._relay.off()
        else:
            print(f"[eyes] {'ON ' if on else 'OFF'}", flush=True)


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

_STATES = {s.value: s for s in EyeState}


async def _cli(state: EyeState, secs: float | None) -> None:
    async with EyeController() as eyes:
        await eyes.set_state(state)
        if secs is not None:
            await asyncio.sleep(secs)
        else:
            # hold until Ctrl-C
            try:
                await asyncio.Event().wait()
            except (KeyboardInterrupt, asyncio.CancelledError):
                pass


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Control FrustratedBox eye bulbs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="States: off  on  listening  speaking",
    )
    parser.add_argument(
        "state",
        choices=list(_STATES),
        help="Eye state to enter",
    )
    parser.add_argument(
        "--secs",
        type=float,
        default=None,
        metavar="N",
        help="Hold state for N seconds then exit (default: hold until Ctrl-C)",
    )
    args = parser.parse_args()

    try:
        asyncio.run(_cli(_STATES[args.state], args.secs))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
