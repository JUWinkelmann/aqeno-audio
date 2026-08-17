# AQENO Reference Hardware — Solderless Prototype

## Objective
Build a robust, fully solderless Reference prototype around Raspberry Pi 4B while keeping every input behind replaceable platform adapters.

## Reference v0
- Raspberry Pi 4B
- 7-inch Raspberry Pi touch display already available to the project
- USB-C mains power or suitable commodity power bank
- plug-in I2C/Qwiic/STEMMA-QT input hardware
- no breadboard as a permanent mechanical component
- no loose Dupont wiring in the final prototype enclosure

## Controls

### Volume / Play-Pause — preferred
**Adafruit I2C STEMMA QT Rotary Encoder, PID 5880 (pre-soldered encoder).**

Why:
- pre-soldered variant requires no soldering;
- rotary + push switch in one control;
- I2C keeps GPIO details out of application logic;
- onboard controllable NeoPixel provides dimmable RGB feedback and true software OFF;
- can connect through STEMMA QT/Qwiic.

Important: the board also has small diagnostic/power LEDs. In the enclosure these should be physically hidden from the user; only the intentional user-facing light should be visible.

### Previous / Next / optional fourth action — preferred prototype
**Adafruit NeoKey 1x4 QT I2C + MX-compatible hot-swap switches + translucent keycaps.**

Why:
- switches plug into Kailh sockets without soldering;
- each key has an individually controllable NeoPixel;
- LEDs can be dimmed or switched off by software;
- mechanical switches are replaceable;
- STEMMA QT connection is solderless.

Mechanical note: the PCB must be fixed to the enclosure and switches supported by the printed front plate. Do not rely on the PCB/socket alone to absorb child-force. Choose robust MX-compatible switches and captive/secure keycaps.

Recommended mapping:
1. Previous
2. optional/context/reserved
3. Next
4. initially unused or prototype-only

The production design may later reduce this to two dedicated rugged buttons after user testing.

## Raspberry Pi I2C connection
Use an **Adafruit Pi STEMMA QT breakout (PID 6365)** or equivalent Pi-compatible Qwiic adapter that plugs onto the Pi GPIO header without soldering. Chain devices with short locking JST-SH STEMMA QT/Qwiic cables.

## NFC
Do not purchase a permanent NFC module until the first vertical slice is working with simulated NFC. The NFC reader must eventually be:
- pre-assembled;
- solderless to install;
- Linux/Raspberry-Pi friendly;
- mountable behind a non-metallic enclosure surface;
- supported by a clean adapter.

PN532 remains the preferred technology family, but the exact board is a feasibility decision. Avoid Grove PN532 variants that require cutting/soldering to change interface mode.

## LEDs and visual policy
Hardware LEDs are not decoration by default.

Software must support:
- OFF;
- very low night-safe brightness;
- normal interaction brightness;
- semantic colours only where they add information.

Night/Dark-Room forces all user-facing LEDs to OFF. Diagnostic LEDs that cannot be software-disabled must be hidden inside the enclosure so they cannot illuminate the room.

## Audio
For the first software slice, use any already-available USB audio device or HDMI/known working output. Do not lock the architecture to a DAC HAT yet.

Before enclosure freeze, choose a solderless USB audio solution or preassembled amplifier/speaker module with locking connectors. Audio hardware must not consume the only practical connector path for Reference controls.

## Power
Reference input is standard USB-C power to the Pi. Mobile use should work from a suitable third-party power bank; AQENO must not require a proprietary battery.

Power-bank compatibility must be tested for:
- required sustained current;
- behaviour at low/idle load;
- wake/restart behaviour;
- ability to power Pi + display + audio + controls.

## Mechanical robustness
- boards screwed into printed bosses/standoffs;
- strain relief on USB/power/audio cables;
- JST/Qwiic/Grove-style locking/friction connectors inside enclosure;
- no exposed PCBs;
- no loose breadboard;
- buttons supported by front panel;
- encoder shaft/knob mechanically supported;
- serviceable enclosure using screws rather than permanent glue where practical.

## Buy now vs later

### Buy now
- Pi STEMMA QT/Qwiic GPIO adapter;
- pre-soldered RGB rotary encoder module;
- NeoKey 1x4 QT;
- 3–4 robust MX-compatible switches;
- 3–4 translucent/shine-through keycaps;
- several short STEMMA QT/Qwiic cables;
- M2.5/M3 screw/standoff assortment for printed prototypes.

### Buy after first vertical slice
- NFC reader + tags;
- final audio amp/speakers;
- power bank dedicated to AQENO;
- final knobs/keycaps;
- enclosure hardware.

This deliberately avoids spending money on parts whose form factor should be determined by UX testing.
