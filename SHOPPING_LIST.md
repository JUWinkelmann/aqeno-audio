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
| 1 | Adafruit VEML7700 ambient-light sensor, PID 4162 | Ambient light; RH1 reference for the VCNL4040 comparison |

The original components are physically present. The MiniAmp and ready-made adapters are the selected
replacement audio path; receipt/exact revision must be recorded from the units before they are called
on hand. Selection never counts as electrical or acoustic validation.

## Buy only when required for assembly or verification

- suitable standoffs, fasteners and strain relief for the chosen mechanical layout;
- a suitable stationary USB-C power supply if none is already available;
- a sound-level meter suitable for the child-volume calibration procedure.

## Do not buy yet

Nothing on this list is ordered before the AQENO Hardware Interaction Contract (ADR 0026) has been
tested on RH1. The order of work is: interaction → contract → requirements → RH1 test → component.

- **second rotary encoder for SELECT** — required for the complete touch-free journey, and precisely
  the thing not to buy reflexively. Choose against the AQENO Rotary Control Contract (ADR 0026 § 7),
  not because a board is already in the drawer. Check first whether a second Adafruit 5880's I²C
  address can be changed without bridging solder jumpers; if it cannot, it fails the no-solder gate.
- **VCNL4040 proximity/ambient breakout** — not before the bus and mounting contract is settled and
  the VEML7700 baseline exists.
- **NFC module** — simulate NFC first, then choose a genuinely solderless PN532 implementation.
  Validate read range over the whole flat object area, with a card and a standing object.
- **AMOLED panel** — a preference, not a dependency (ADR 0025 § 1). No order.
- **magnets for object positioning** — no arrangement is specified and the electromagnetic
  interaction is unmeasured.
- **battery/power bank** — test stationary first; later validate common power banks.
- **expensive custom arcade switches** — wait until physical-control testing tells us button size
  and force.
- **cables and adapters on suspicion** — buy against a recorded need in the RH1 resource map.
- **any production carrier board or enclosure hardware** — RH1 is not the product.

## Target control direction — do not buy yet

ADR 0026 fixes the control vocabulary (SELECT encoder, PREVIOUS, NEXT, VOLUME encoder, HOME) and the
abstract Rotary Control Contract; `docs/hardware/HARDWARE_REFERENCE.md` records the quality
expectations. **No component is selected**, and nothing here is ordered while RH1 validation is the
active work. Maker breakouts are prototype implementations, never the definition of AQENO hardware.

## Control layout for the prototype — buildable from stock

```text
[ SELECT: focus / press select ]  [ PREV ] [ NEXT ]  [ HOME ]  [ VOL: volume / press Play-Pause ]
        missing                   socket 0  socket 1  socket 3   Adafruit 5880
```

**Four of the five controls need no purchase.** PREVIOUS, NEXT and HOME are three Cherry MX switches
in the NeoKey's hot-swap sockets, and several switches plus transparent keycaps are already on hand.
Socket 2 is deliberately left empty so HOME is separated from the transport pair by touch. Only
SELECT is missing, and it is simulated until an encoder is chosen against the contract above.

## LED rule
All user-visible LEDs must be software-controllable in brightness and support true OFF. In Night/Dark-Room they are OFF. Any unavoidable board power/diagnostic LEDs are hidden inside the enclosure.
