# AQENO Prototype Inventory and Remaining Purchases

This list is for the **Reference prototype**, not final production hardware.

## Acquired / selected for RH1

| Qty | Item | Purpose |
|---:|---|---|
| 1 | Raspberry Pi 4B | AQENO Core |
| 1 | FREENOVE 7-inch touchscreen | Device UI and touch |
| 1 | Adafruit rotary encoder PID 5880 | Volume, Play/Pause press and RGB feedback |
| 1 | Adafruit NeoKey 1x4 QT PID 4980 | Previous/Next MX buttons and NeoPixels |
| several | CHERRY MX2A Brown RGB, 3-pin (MX2A-G1NA) | Physical buttons; initially two used |
| 1 pack of 10 | Adafruit transparent MX keycaps PID 4956 | Light-transmitting keycaps |
| 1 | SparkFun Qwiic SHIM DEV-15794 | Solderless Pi I2C/Qwiic connection |
| 1 | Adafruit STEMMA QT/Qwiic Hub PID 5625 | I2C distribution |
| 3 | Adafruit 300 mm STEMMA QT/Qwiic cables PID 5384 | Solderless bus wiring |
| 1 | HiFiBerry MiniAmp, stereo 2 x 3 W | RH1 audio amplifier; preassembled, no soldering |
| 2 | Ready-made JST-PH2.0-to-speaker-terminal adapter | Replaceable speaker connection without soldering/crimping |
| 2 | QUARKZMAN 3 W / 4 ohm speakers, 44 x 31 x 15 mm | Stereo output |
| 2 | Supplied JST-PH 2.0 leads, 100 mm | Removable speaker connection |

The original components are physically present. The MiniAmp and ready-made adapters are the selected
replacement audio path; receipt/exact revision must be recorded from the units before they are called
on hand. Selection never counts as electrical or acoustic validation.

## Buy only when required for assembly or verification

- suitable standoffs, fasteners and strain relief for the chosen mechanical layout;
- a suitable stationary USB-C power supply if none is already available;
- a sound-level meter suitable for the child-volume calibration procedure.

## Do not buy yet
- NFC module: simulate NFC first, then choose a genuinely solderless PN532 implementation.
- battery/power bank: test stationary first; later validate common power banks.
- expensive custom arcade switches: wait until Kids Early physical-control testing tells us button size/force.

## Target control direction — do not buy yet

ADR 0024 fixes the target vocabulary (NAV encoder, VOL encoder, momentary centre-off transport
rocker) and `docs/hardware/HARDWARE_REFERENCE.md` records the quality expectations. No component is
selected, and nothing here is ordered while RH1 validation is the active work.

The RH1 test layout is LEFT · NAV · RIGHT · VOL, with the existing Cherry MX switches as LEFT/RIGHT
and the acquired Adafruit 5880 as VOL/Play. NAV needs a second suitable encoder and is simulated
until one exists. Verify first whether a second 5880's I²C address can be changed without bridging
solder jumpers — if it cannot, that conflicts with the no-solder gate, and the call is yours.

## Recommended control layout for prototype

`[ LEFT: back ]   [ NAV: focus / press select ]   [ RIGHT: forward ]   [ VOL: volume / press Play-Pause ]`

NAV is not yet present on RH1. The remaining NeoKey positions stay available for experiments and are
not part of the committed product UI.

## LED rule
All user-visible LEDs must be software-controllable in brightness and support true OFF. In Night/Dark-Room they are OFF. Any unavoidable board power/diagnostic LEDs are hidden inside the enclosure.
