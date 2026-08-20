# FrustratedBox — Bill of Materials

**Architecture:** Thin edge node (Pi 5) inside the box handling presence detection, audio I/O, VAD, eye-bulb control, and the conversation state machine; STT (Whisper) + LLM + TTS run on my GPU backend over WiFi. Battery-powered, weatherproofed, camera-ready for future upgrades.


![Hand-drawn schematic](schematic.png "Rough schematic of the build")


---

## Core compute

| Qty | Item | Est. € | Purpose / notes |
|---|---|---|---|
| 1 | Raspberry Pi 5, 8GB | | Edge node. |

## Connectivity (can be skipped if the talking box is close to home router; for me it will be sitting outside of the house on Halloween, so I wanted something more reliable)

| Qty | Item | Est. € | Purpose / notes |
|---|---|---|---|
| 1 | Alfa USB WiFi adapter (this is what I had :) |  | We need something more powerful than Raspberry Pi's internal WiFi |

## Audio

| Qty | Item | Est. € | Purpose / notes |
|---|---|---|---|
| 1 | ReSpeaker Mic Array v3.0 | | USB plug-and-play, beamforming + **hardware AEC**, has line-out |
| 1 | TPA3116D2 class-D amp board (12V) |  | Runs straight off the 12V battery |
| 1 | Weatherproof/marine speaker (you can settle on just any speaker if there's no risk of rain), 4–8Ω, 20–30W but I used 100W!|  | Output; fed from the mic array's 3.5mm line-out -> then amp |

## Presence sensing (not yet implemented! -- TBC)

| Qty | Item | Est. € | Purpose / notes |
|---|---|---|---|
| 1 | VL53L1X laser ToF module (I2C, ~4m) | | Triggers on approach along a single beam line |

## Eyes (bulbs)

| Qty | Item | Est. € | Purpose / notes |
|---|---|---|---|
| 2 | 12V 21W PY21W/N581 (BAU15s) or similar automotive incandescent bulb + socket | | Retro/scary look; filament gives a natural fade on each blink. ~1.75A each (3.5A the pair), wired in parallel. (12V LED-filament is the cooler/efficient alternative, but somehow I loved the fading of old blinker bulbs |
| 1 | Relay module | | Pi GPIO switches both bulbs on/off. Use the NO contact; most modules are active-low |

## Power & distribution

| Qty | Item | Est. € | Purpose / notes |
|---|---|---|---|
| 1 | ECO-WORTHY 12V 20Ah LiFePO4 (I happened to have this one, you can use any similar 12V battery) | | Main supply |
| 1 | XL4015 buck (5A) | | Pi 5 rail. Set to 5.1V with a meter *before* connecting; verify it holds ≥5.0V under Pi load |
| 1 | 4–6 way blade fuse block; use one with ground bus if you have, but I used a piece of old lamp for the ground rail :P | | 12V distribution: fused branches to amp, Pi buck, and the eyes (bulbs) |
| 1 | Inline fuse holder + assorted fuses (~7.5A main) |  | Fuse the positive lead close to the battery |
| 1 | Power switch (12V, ≥10A) |  | Main on/off on positive line |
| some | Hook-up wire — 16AWG main, 18AWG branches |  | |
| some | Connectors, lugs, heatshrink | 5 | |


**Note A — AEC routing (important).** The ReSpeaker's hardware echo cancellation works by referencing the audio it plays through *its own* output. So TTS playback must go **out through the mic array's 3.5mm line-out → amp**, not through a separate USB DAC. Routing audio elsewhere loses hardware AEC (you'd fall back to software AEC). This is why a separate output DAC is *not* in this BoM.

**Note B — Pi 5 has no 3.5mm jack.** Audio output for this build comes from the ReSpeaker, per Note A.

**Note C — Fuse sizing.** All blade/mini-blade type (same type as in your car). Main fuse at the battery: **7.5A** (whole system <50W ≈ 4A at 12V, headroom for peaks, protects the 16AWG main lead). Per-branch in the block: **amp 5A** (3A if a small speaker), **Pi buck 3A** (~2.3A input at worst-case Pi load), **eyes 5A slow-blow** (two 21W bulbs draw ~3.5A continuous, so 2A would blow).

**Note D — WiFi.** The Pi 5's onboard WiFi has no external-antenna connector, so I'm using the Alfa USB adapter. Data demand here is tiny (compressed audio + text API ≈ tens of kbps), so aim for a *stable* link, not a fast one — connect on the **2.4GHz** band for better wall penetration/range. In my case I mounted the antenna outside the enclosure. Driver path depends on the Alfa's chipset: Atheros/MediaTek are in-kernel (plug-and-play); Realtek 8812AU/8814AU needs a different driver, you need to figure out depending on the adapter you have/buy.

**Note H — Eyes (relay + bulbs).** A Pi GPIO drives the relay module's IN pin (3.3V is fine on opto-isolated modules). Wired both bulbs in parallel on the relay's **NO (normally-open)** contact, in series with the 5A slow-blow 12V branch, so a de-energized relay = eyes dark. No series resistor (which I was considering before as I initially thinking LEDs, not bulbs) — the filament runs directly across 12V. Most modules are **active-low**, but the module in this build is **active-high** (see `eyes.py`), and the GPIO floats during boot, so set it de-energized immediately in software — with gpiozero on the Pi 5: `OutputDevice(pin, active_high=True, initial_value=False)` keeps the eyes off at startup (use `active_high=False` if your module is the common active-low kind). The relay clicks loud when switching which initially made me mad, but I actually find it very much in the box's character now! I'll re-think this when this project becomes anything more serious than a Helloween prompt.
