# AQENO Prototype Shopping List — no soldering

This list is for the **Reference prototype**, not final production hardware.

## Buy now

| Qty | Item | Purpose | Approx. observed price |
|---:|---|---|---:|
| 1 | Adafruit Pi STEMMA QT Breakout PID 6365 or equivalent | Solderless Pi I2C/Qwiic connection | ~US$2.50 |
| 1 | Adafruit I2C QT Rotary Encoder **PID 5880 pre-soldered** | Volume + push Play/Pause + RGB LED | ~€8–15 depending retailer |
| 1 | Adafruit NeoKey 1x4 QT I2C | Hot-swap physical buttons + 4 controllable RGB LEDs | ~€10–14 |
| 3–4 | MX-compatible switches | Previous / Next / spare | ~€1 each upward |
| 3–4 | translucent/shine-through MX keycaps | Let controlled LED light through | a few euros |
| 3–4 | STEMMA QT/Qwiic cables, 50–200 mm | Internal plug connections | ~€1 each |
| 1 set | M2.5/M3 screws + brass/plastic standoffs | Robust printed enclosure mounting | ~€8–15 |
| 1 | suitable USB-C PSU if none available | Stationary power | use quality 5 V supply suitable for Pi 4 |

Already available: Raspberry Pi 4B + 7-inch display.

## Do not buy yet
- NFC module: simulate NFC first, then choose a genuinely solderless PN532 implementation.
- battery/power bank: test stationary first; later validate common power banks.
- final speakers/amplifier: choose after enclosure/audio requirements.
- expensive custom arcade switches: wait until Kids Early physical-control testing tells us button size/force.

## Recommended control layout for prototype

`[ Previous ]   [ illuminated rotary: Volume / press Play-Pause ]   [ Next ]`

A fourth NeoKey position remains available for experiments but is not part of the committed product UI.

## LED rule
All user-visible LEDs must be software-controllable in brightness and support true OFF. In Night/Dark-Room they are OFF. Any unavoidable board power/diagnostic LEDs are hidden inside the enclosure.
