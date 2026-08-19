# AQENO Hardware Inventory

**Updated:** 2026-08-19
**Scope:** AQENO Reference Hardware 1 (RH1) — the prototype, not the product.
**Status:** **RH1 PROCUREMENT FREEZE active.** `BUY NOW = nothing.`

This is the **single canonical record of what AQENO physically owns, ordered, deferred and paid**.
Nothing else in the repository maintains a parts list. `docs/hardware/HARDWARE_REFERENCE.md` is the
companion and answers a different question — *why* a component is used, what interfaces and limits
it has, and which tests it still owes. It does not repeat this table.

## The two dimensions

Every component answers two independent questions, and they must never be merged again:

> **Do we have it?**  ·  **What role does it play in the product?**

| `possession_status` | Meaning |
|---|---|
| `OWNED` | physically here |
| `ORDERED` | bindingly ordered, not yet received |
| `NONE` | not ordered |

| `product_role` | Meaning |
|---|---|
| `RH1_PLATFORM` | the prototype's computer/display base |
| `RH1_PROTOTYPE` | prototype implementation of a contract requirement |
| `RH1_INFRASTRUCTURE` | wiring, mounting, power — enables the build, says nothing about the product |
| `EVALUATION` | here to be measured or compared, probably not in a later reference BOM |
| `TRANSITIONAL` | enables a capability now, explicitly **not** the target technology |
| `DEFERRED_EVALUATION` | accepted for RH1, deliberately not procured yet |
| `FUTURE_UNDECIDED` | the capability is decided, the component is not |

The separations that this table exists to protect:

```text
ORDERED       != PRODUCT_STANDARD
RH1           != REFERENCE_HARDWARE
TRANSITIONAL  != TARGET_TECHNOLOGY
EVALUATION    != REQUIRED_COMPONENT
APPROVED_FOR_RH1 != APPROVED_FOR_PRODUCT
```

## Inventory

### Compute and display

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 | Raspberry Pi 4B | Raspberry Pi 4 Model B; RAM variant to record | `OWNED` | `RH1_PLATFORM` |
| 1 | 7-inch touchscreen | FREENOVE; 800 × 480, MIPI DSI; exact SKU/revision to record | `OWNED` | `RH1_PLATFORM` |

RH1 has touch. AQENO does not require it (ADR 0024 § 1); the panel's touch capability is itself an
`EVALUATION` subject — the box must be validatable with touch ignored.

### Controls

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 | Rotary encoder — **VOLUME** | Adafruit 5880, STEMMA QT | `ORDERED` | `RH1_PROTOTYPE` |
| 1 | Rotary encoder — **SELECT** | SparkFun Qwiic Twist DEV-15083 | `ORDERED` | `RH1_PROTOTYPE` |
| 1 | Key board for PREVIOUS · NEXT · HOME | Adafruit NeoKey 1x4 QT 4980 | `ORDERED` | `RH1_PROTOTYPE` |
| 10 | Key switches | CHERRY MX2A-G1NA Brown RGB, 3-pin | `ORDERED` | `RH1_PROTOTYPE` |
| 10 | Transparent MX keycaps | Adafruit 4956 | `ORDERED` | `RH1_PROTOTYPE` |
| 1 | Aluminium knob, 32 × 13 mm, 6 mm bore, grub screw | — | `ORDERED` | `EVALUATION` |
| 2 | Aluminium knob with illuminated ring, 22.2 mm, black | Elecrow CQA231128PB13 | `ORDERED` | `EVALUATION` |

Three of the ten switches are used (PREVIOUS, NEXT, HOME). The Qwiic Twist is
`APPROVED_FOR_RH1`, which is **not** `APPROVED_FOR_PRODUCT`. Both knob types are ergonomics samples;
the Elecrow knobs' fit and illumination on a Twist are `REAL_TEST_REQUIRED`
(`HARDWARE_REFERENCE.md` § Encoder cap evaluation).

### I²C / Qwiic infrastructure

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 | Pi → Qwiic adapter, 3.3 V regulator | SparkFun Qwiic SHIM DEV-15794 | `ORDERED` | `RH1_INFRASTRUCTURE` |
| 1 | 5-port passive Qwiic hub | Adafruit 5625 | `ORDERED` | `RH1_INFRASTRUCTURE` |
| 3 | Qwiic/STEMMA QT cable, 300 mm | Adafruit 5384 | `ORDERED` | `RH1_INFRASTRUCTURE` |
| 3 | Qwiic/JST-SH cable, 100 mm | Elecrow ACC01495C | `ORDERED` | `RH1_INFRASTRUCTURE` |

**Six cables total after delivery, and that is sufficient.** Normal RH1 operation needs five; the
later sensor comparison needs six plus one daisy-chain hop. **Do not buy further Qwiic cables or a
second hub.** Capacity and address map: `HARDWARE_REFERENCE.md` § Qwiic capacity and cabling.

### Audio

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 | Stereo I²S amplifier | HiFiBerry MiniAmp, 2 × 3 W | `ORDERED` | `RH1_PROTOTYPE` |
| 2 | Mini speaker, 3 W / 4 Ω | QUARKZMAN, 44 × 31 × 15 mm | `OWNED` | `RH1_PROTOTYPE` |
| 20 pairs | JST-PH 2.0 lead, 2-pin, 80 mm | GTIWUNG | `ORDERED` | `RH1_INFRASTRUCTURE` |

JST-PH leads are not a universal connector: **check pinout and current rating per use**. A later
AQENO may use an entirely different audio architecture.

### Sensing

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 | Ambient-light sensor | Adafruit VEML7700, PID 4162 | `ORDERED` | `RH1_AMBIENT_SENSOR` + `EVALUATION` |
| — | Ambient light + proximity | Adafruit VCNL4040, PID 4161 | `NONE` | `DEFERRED_EVALUATION` |

The VEML7700 is RH1's **current, real ambient-light sensor** — not a placeholder. It supports
brightness thresholds, dark/night behaviour and real bedroom measurements today.

The VCNL4040 is `APPROVED_FOR_RH1` but **unavailable and deliberately not ordered**. Until it exists,
`AmbientLight` is provided by the VEML7700 and **proximity simply does not exist on RH1**. That is
not degraded operation: AQENO must work completely without proximity, which is a comfort capability
only (ADR 0026 § 10).

### Tag input

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 | USB RFID reader, 125 kHz | EM4100/EM4102 class; **exact model not yet verified** | `OWNED` | `TRANSITIONAL` |

> **This is not AQENO's NFC solution and it is not 13.56 MHz.**

It exists so tag-based interaction — tag seen → identifier → AQENO assignment → semantic action —
can be developed now, without a purchase. Domain and Application must not depend on it. The device
must be identified physically before any adapter is written (`HARDWARE_REFERENCE.md` § Transitional
tag reader).

### Mechanical

| Qty | Component | Identifier | Possession | Product role |
|---:|---|---|---|---|
| 1 set | M3 screws and standoffs, 100 pieces | justPi Set B | `ORDERED` | `RH1_INFRASTRUCTURE` |

## Costs

Verified order values only. Shipping is listed separately, unknown prices are left blank rather than
guessed, and **no product BOM cost may be derived from these maker prices**.

| Order | Goods | Shipping | Total |
|---|---:|---:|---:|
| Botland (5880, 4980, 4956, SHIM, hub, 3 × 300 mm cable, M3 set) | 57.90 € | 4.99 € | 62.89 € |
| HiFiBerry MiniAmp | 23.70 € | 5.95 € | 29.65 € |
| Cherry MX2A Brown RGB × 10 | 6.00 € | 5.95 € | 11.95 € |
| BerryBase (Qwiic Twist, 3 × 100 mm cable, 2 × Elecrow knob) | 40.60 € | — | — |
| Amazon items (speakers, JST-PH leads, 32 mm knob, VEML7700, USB RFID reader) | not recorded | — | — |

BerryBase line items: Qwiic Twist 25.90 €, 3 × Elecrow 100 mm cable 5.70 €, 2 × Elecrow illuminated
knob 9.00 €. Shipping for that order is not recorded here because the previously quoted 4.95 €
applied to a different basket.

## Procurement freeze

> **BUY NOW = nothing.**

No further hardware is procured until the ordered components arrive and the first real RH1 build has
happened. Buying "just in case" is what this freeze exists to stop.

**The only exception** is a concretely demonstrated missing connecting part that blocks the build.
Then, in order: document the problem → check whether owned hardware already solves it → determine
the minimal solution → only then propose a purchase.

### Do not buy now

VCNL4040 (deferred, § Sensing) · PN532 · PN7160 or any NFC reader · further Qwiic cables · a second
Qwiic hub · another Pi→Qwiic adapter · a second Adafruit 5880 · breadboard · Dupont wire · an optical
cover or window material for a sensor · magnets · a PREVIOUS/NEXT rocker · further Cherry MX switches
· further keycaps · another audio amplifier · an AMOLED panel · another SBC · any production carrier,
enclosure or power hardware.

### Buy only when a recorded need proves it

A stationary USB-C power supply if none is available; a sound-level meter for the child-volume
calibration procedure; standoffs or strain relief the M3 set does not already cover.

## Future / undecided

The capability is decided; the component is not. Nothing here is a shopping list.

Final NFC controller, antenna and object area · magnetic positioning · final display · AMOLED ·
final SBC · production encoders and caps · final PREVIOUS/NEXT mechanism (possibly one centre-off
rocker) · production audio hardware · power architecture · a carrier board.

## What RH1 must not be read as

RH1 uses maker hardware to test interaction hypotheses. It does **not** follow that AQENO needs a
Raspberry Pi, Qwiic, a NeoKey, a Qwiic Twist, an Adafruit 5880, a VEML7700, a HiFiBerry, Cherry MX
switches, touch, or 125 kHz RFID.

What RH1 exists to validate is abstract: SELECT · PREVIOUS · NEXT · VOLUME · HOME, eyes-free
operation, tactile differentiation, physical-first interaction, **DARK means zero visible light**,
ambient-aware behaviour, later optional proximity-assisted illumination, tag-based shortcuts, a flat
object area, and hardware-independent semantic interaction.

## LED rule

All user-visible LEDs must be software-controllable in brightness and support true OFF. Under
Night/Dark-Room policy they are OFF. Any unavoidable board power or diagnostic LED is hidden inside
the enclosure.
