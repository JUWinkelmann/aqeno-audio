# AQENO Reference Hardware 1

**Identifier:** AQENO Reference Hardware 1 (`RH1`)

**Status:** Prototype platform; controls adapter implemented, pending on-device validation; MiniAmp
selected as RH1 audio, physical receipt/integration evidence still to record

**Date:** 2026-08-19

## Role

Reference Hardware 1 is the first concrete platform on which AQENO is developed, measured and
tested. AQENO should work exceptionally well on it. It is not the definition of AQENO and does not
make Raspberry Pi 4, a 7-inch touchscreen, Qwiic, one encoder, four MX switches or this control
mapping permanent Core requirements.

> Reference Hardware proves AQENO. It does not define AQENO.

Since ADR 0024 that statement is binding for the controls as well: the Cherry MX keys, the single
Qwiic encoder and the touch panel are **prototype input hardware**. They do not describe the target
product layout, and the software is developed against the AQENO control contract (SELECT, PREVIOUS,
NEXT, VOLUME, HOME — ADR 0026 § 2) rather than against what happens to be plugged in.

ADR 0026 fixes the order of work, and it is the reason this document is a record rather than a plan:

```text
product interaction → hardware interaction contract → mechanical/electrical requirements
   → RH1 test → component decision
```

Future hardware may omit the screen, use different controls or provide a more display-oriented
experience. Domain and application code consume user intentions and product state; adapters own
boards, buses, addresses, pins and physical mappings. No generic hardware-profile or persona system
is implied.

## RH1 components

**The canonical parts list lives in `INVENTORY.md`** — quantities, possession status, product role
and costs. It is not repeated here, so that the two documents cannot drift apart again. This
document answers the other questions: why a component is used, what interfaces and limits it has,
and which tests it still owes.

Technical caveats that belong to this document rather than to the inventory:

- the display's exact SKU/revision and the Pi's RAM variant are recorded from the physical units;
  the reported 800 × 480, 60 Hz, capacitive 5-point touch and MIPI DSI connection are the RH1 design
  target and establish neither authoritative panel-off nor Linux display-server behaviour;
- the MiniAmp uses the kernel-supported `hifiberry-dac` overlay; its actual ALSA presentation,
  channel arrangement and safe acoustic range still require RH1 validation;
- ordering or owning a component is never electrical, acoustic or ergonomic validation;
- unknown inventory details stay unknown rather than guessed.

## Prototype topology

```text
Raspberry Pi 4B
│
├── 7-inch Touch Display
│
├── HiFiBerry MiniAmp on the 40-pin header
│   ├── JST-PH2.0 adapter → QUARKZMAN 3 W / 4 ohm speaker (left)
│   └── JST-PH2.0 adapter → QUARKZMAN 3 W / 4 ohm speaker (right)
│
├── candidate PN532 NFC reader via SPI (not acquired / not Reference-supported)
│
└── SparkFun Qwiic SHIM DEV-15794
    │
    └── Adafruit Qwiic Hub 5625
        │
        ├── Adafruit 5880 rotary encoder
        │   ├── rotate → relative volume change
        │   ├── press  → play/pause
        │   └── RGB    → restrained contextual feedback
        │
        ├── Adafruit NeoKey 1x4 4980
        │   ├── socket 0 → PREVIOUS
        │   ├── socket 1 → NEXT
        │   ├── socket 2 → deliberately empty; tactile gap before HOME
        │   └── socket 3 → HOME
        │
        ├── SparkFun Qwiic Twist DEV-15083
        │      └── SELECT: rotate → focus/value, press → activate
        │
        └── Adafruit VEML7700 4162
               └── ambient light

    Four downstream devices; the hub's four ports fit exactly.
    A later VCNL4040 comparison adds a fifth device and needs one
    daisy-chain hop — not a second hub.
```

The Qwiic SHIM is the thin, HAT-stackable DEV-15794. It carries the Pi I2C bus and power beside the
MiniAmp; it does not consume any of the MiniAmp's I2S/control GPIOs.

## RH1 resource map

| Resource | Physical pins/interface | Owner(s) | State |
|---|---|---|---|
| MIPI DSI | dedicated DSI connector | FREENOVE display | exclusive, no GPIO-header conflict |
| I2C1 SDA/SCL | GPIO2/3, pins 3/5 | Qwiic SHIM → hub → all Qwiic devices (§ Qwiic address map) | shared bus; every planned address distinct |
| I2S PCM clock/data | GPIO18-21, pins 12/35/38/40 | HiFiBerry MiniAmp | exclusive to audio |
| amplifier mute | GPIO16, pin 36 | HiFiBerry MiniAmp | exclusive/reserved by MiniAmp |
| amplifier shutdown | GPIO26, pin 37 | HiFiBerry MiniAmp | exclusive/reserved by MiniAmp |
| HAT identity | GPIO0/1, pins 27/28 | HAT EEPROM convention | reserved; Qwiic controls do not use it |
| 5 V | pins 2/4 | MiniAmp power; Qwiic SHIM regulator input | shared power rail, not a signal conflict |
| 3.3 V | Qwiic regulator output | Qwiic peripherals | shared Qwiic power; current budget still to validate |
| GND | GPIO-header ground pins | MiniAmp + Qwiic SHIM | shared reference |
| remaining GPIO | all not named above | unassigned | unused by RH1 |

This map follows HiFiBerry's MiniAmp GPIO contract: GPIO18-21 are I2S, GPIO16 is mute and GPIO26 is
shutdown. A shared rail or bus is not a conflict. Any new module must be checked against this table
before it is called RH1-compatible.

### Qwiic address map

Verified against vendor documentation on 2026-08-19, not assumed. Every planned RH1 device has a
distinct address, so **no bus conflict exists** and no multiplexer is required. The earlier open
question about a second Adafruit 5880's address jumper is moot: RH1 uses no second 5880.

| Device | Address | Possession | Evidence |
|---|---|---|---|
| NeoKey 1x4 (4980) | `0x30` | ORDERED | Adafruit default; in `adapters/input/i2c_seesaw.py` |
| Rotary encoder (5880) | `0x36` | ORDERED | Adafruit default; in `adapters/input/i2c_seesaw.py` |
| Qwiic Twist (DEV-15083) | `0x3F` (jumper `0x3E`; software `0x08`–`0x77`) | ORDERED | SparkFun product page |
| VEML7700 (4162) | `0x10` | ORDERED | Adafruit CircuitPython library default; in `adapters/ambient_light/veml7700.py` |
| VCNL4040 (4161) | `0x60` | NONE — deferred | Adafruit CircuitPython library default |

### Qwiic capacity and cabling

The Adafruit 5625 hub is a **5-port passive hub whose ports are all electrically parallel**, so one
port is consumed by the uplink from the Qwiic SHIM and **four downstream ports remain**. The SHIM
itself has a single Qwiic connector and carries a 3.3 V regulator fed from the Pi's 5 V rail.

| Configuration | Devices | Hub ports | Cables |
|---|---:|---|---:|
| RH1 as ordered | NeoKey, 5880, Twist, VEML7700 | 4 of 4 — exactly fits | 5 |
| Later sensor comparison | the above **plus** VCNL4040 | one short | 6 |

The comparison configuration therefore needs **one daisy-chain hop** through a device's second Qwiic
connector rather than a second hub. The Twist and the VCNL4040 breakout each have two connectors
(vendor-confirmed); confirm the same for the NeoKey, 5880 and VEML7700 from the units.

Cable requirement: **6 total, and 6 are on order** — 3 × 300 mm plus 3 × 100 mm. The stock is
sufficient for both configurations and **no further Qwiic cable or hub is to be bought**
(`INVENTORY.md` § Procurement freeze). The 300 mm cables cover the long runs; verify a 100 mm length
actually reaches before relying on it, since the enclosure layout is not fixed.

Primary vendor evidence for this section:
[Qwiic Twist product page](https://www.sparkfun.com/products/15083),
[Qwiic Twist hookup guide](https://learn.sparkfun.com/tutorials/qwiic-twist-hookup-guide/all),
[VCNL4040 breakout](https://www.adafruit.com/product/4161),
[STEMMA QT 5-port hub](https://www.adafruit.com/product/5625),
[Qwiic SHIM](https://www.sparkfun.com/sparkfun-qwiic-shim-for-raspberry-pi.html).

Primary vendor evidence: [MiniAmp data sheet](https://www.hifiberry.com/docs/data-sheets/datasheet-miniamp/),
[HiFiBerry GPIO use](https://www.hifiberry.com/docs/hardware/gpio-usage-of-hifiberry-boards/),
[HiFiBerry Linux configuration](https://www.hifiberry.com/docs/software/configuring-linux-3-18-x/),
[SparkFun Qwiic SHIM](https://www.sparkfun.com/sparkfun-qwiic-shim-for-raspberry-pi.html) and
[Adafruit 5880 pinout](https://learn.adafruit.com/adafruit-i2c-qt-rotary-encoder/pinouts).

## RH1 audio platform configuration

Raspberry Pi OS Lite uses its in-kernel driver with `dtoverlay=hifiberry-dac`; onboard audio is
disabled with `dtparam=audio=off`. AQENO selects the ALSA device by stable card ID
`plughw:CARD=sndrpihifiberry,DEV=0`, never by `hw:0`/`hw:1`. Logical volume remains GStreamer/AQENO
pipeline gain because the MiniAmp has no integrated hardware volume control. The reference platform
configuration lives under `deploy/rh1/`; Domain and Application do not mention HiFiBerry.

The existing first-boot volume (40%), Kids ceiling (70%) and Night ceiling (35%) remain conservative
software defaults. They are not acoustic safety certification; final limits require measurements
with the assembled MiniAmp, speakers and enclosure.

## No-solder acceptance gate

RH1 must be assemblable without soldering or crimping. Audio uses the preassembled MiniAmp and
ready-made JST-PH2.0-to-speaker-terminal adapters; controls use Qwiic and socketed switches. No
breadboard or Dupont wiring is accepted for the audio path. Modules stay connectorized and
replaceable.

Before another component becomes RH1-compatible, record: electrical compatibility; GPIO/bus use;
I2C address where relevant; power; mechanical fit; connector types; solder/crimp requirements;
Linux/kernel support; availability/replaceability; and interaction with every resource in the RH1
map. This is an acceptance checklist, not a hardware framework.

The hub creates physical connection capacity, not product scope. Reserved keys and free branches
remain unused until a tested interaction needs them.

## Reference interaction mapping

| Physical event | Adapter output | RH1 default action |
|---|---|---|
| 5880 counter-clockwise/clockwise | `volume_encoder.rotate_left` / `.rotate_right` | Volume down/up |
| 5880 short press | `volume_encoder.short_press` | Play/Pause |
| 5880 long press (≥800 ms) | `volume_encoder.long_press` | unassigned; long press is setup/service only (ADR 0024 § A2) |
| Twist counter-clockwise/clockwise *(adapter pending delivery)* | `select_encoder.rotate_left` / `.rotate_right` | Move focus / change a value |
| Twist short press *(adapter pending delivery)* | `select_encoder.short_press` | Activate the focused item |
| NeoKey socket 0 short press | `previous.short_press` | previous item in content order |
| NeoKey socket 1 short press | `next.short_press` | next item in content order |
| NeoKey socket 3 short press | `home.short_press` | return to Home |
| Touch | presentation intention / `WakeRequest` as applicable | Contextual Device UI interaction |
| Tag reader presents/removes an identifier | `NfcPresented` / `NfcRemoved`, carrying the identifier | Resolve an AQENO-local token assignment |

The hardware adapter ends at logical input events. The persistent AQENO mapping layer then emits
semantic application intentions. Core code never receives “Cherry key 3”, a GPIO number, Qwiic
address, NeoKey coordinate, EM4100 packet or reader protocol detail. The Adafruit 5880 adapter owns its official seesaw details: default
address `0x36`, push button pin 24 and NeoPixel pin 6. It normalizes the board's reported direction
before anything above the adapter sees left/right.

`PrimaryAction` and `Acknowledge` are plausible future intentions but are not Vertical Slice events.
They must not be added merely to occupy reserve keys or anticipate alternative hardware.

**One naming item is open, deliberately not acted on yet.** The semantic events are still called
`NfcPresented` / `NfcRemoved`, which names a radio technology the transitional 125 kHz reader does
not use. The events already carry nothing but an identifier, so the *boundary* is correct and no
Domain or Application code depends on the reader; only the name is narrower than the concept
(ADR 0013 treats tokens by identifier, not by technology). Rename them when the first real tag
adapter is written — that is the change where the mismatch would otherwise become a lie, and writing
it earlier means churn without a reader.

## Target control direction

Recorded so software and UI can be built against it. **This is not a purchase list and not a
component decision.**

| Control | Role | Semantics |
|---|---|---|
| SELECT rotary encoder with press | navigation and value entry | rotate: move focus or change a value; short press: activate / confirm |
| PREVIOUS | content order | previous track, chapter, section or image (ADR 0009 § 2) |
| NEXT | content order | next track, chapter, section or image |
| VOLUME rotary encoder with press | volume and playback | rotate: volume; short press: play/pause — permanently, never contextual |
| HOME | the way out | return to the familiar starting point; never stops playback; resolves an interruptive state |

Each control means one thing in every state (ADR 0026 § 2), and their spatial relationship is
invariant across AQENO hardware, so muscle memory transfers between devices. No separate OK button,
no BACK control today, no long press or double press in everyday operation (ADR 0024 § A2).
PREVIOUS and NEXT may become one quality momentary centre-off rocker on the target device; that is a
construction change, not a semantic one.

Controls must also feel right, not only work: an encoder with clearly felt detents, a switch or
rocker with a defined actuation point. Inherent physical feedback is preferred over invented cues
(`PRODUCT_FOUNDATION.md` P20), and AQENO does not emit a sound for every physical action.

Quality expectations, without fixing parts: the target device does not use controls that feel like
maker components. High-grade encoders of the Bourns PEC11R or Alps Alpine EC11 class are plausible
candidates, and SELECT and VOLUME should ideally be the **same** electrical and mechanical encoder
type, with different knobs supplying different haptics — fewer spare-part variants, simpler
procurement, simpler carrier PCB, easier repair. The rocker must be a quality momentary centre-off
part, never a latching mains-style switch.

The abstract requirements are the AQENO Rotary Control Contract (ADR 0026 § 7): incremental encoder,
integrated push, clearly felt detents, consistent direction, and a force usable by a child and by a
person with reduced hand strength. A standardised shaft — **6 mm preferred**, because the widest
range of standard caps fits it — keeps caps exchangeable, so one electronics design carries compact
(≈ 24–26 mm), standard (≈ 30–32 mm) and easy-grip (≈ 36–40 mm) ergonomics. These are evaluation
classes, not a dimensional standard. SELECT and VOLUME must be distinguishable by hand through rim
structure, profile or knurling, without either looking like a special aid (P22, P23).

Ergonomics: the binding requirement is that **an ordinary one-handed press must not appreciably move
AQENO on a normal surface** (ADR 0026 § 6). How that is achieved — rubber feet, mass, centre of
gravity, enclosure geometry, actuation force — is mechanical, so controls may also sit on a
well-reachable inclined front face. This replaces the earlier top-surface-only rule. Enclosure design
is explicitly out of scope here; only the requirement is recorded.

### RH1 control plan

The product-shaped RH1 test layout is:

```text
[ SELECT encoder ]   [ MX PREVIOUS ] [ MX NEXT ]   [ MX HOME ]   [ VOL encoder ]
      (missing)         socket 0       socket 1     socket 3      Adafruit 5880
```

**RH1 can carry four of the five controls with hardware already on hand.** The acquired Adafruit 5880
takes VOLUME/Play. PREVIOUS, NEXT and HOME are three Cherry MX switches in the NeoKey's hot-swap
sockets, of which the maintainer has several — no purchase, no soldering. PREVIOUS and NEXT sit
adjacent so the transport pair reads as one pair by hand; socket 2 is deliberately left empty so HOME
is physically separated from them (P22 Tactile identity). That layout is **provisional until the
assembled unit is felt in the dark**, and the socket assignment lives in
`adapters/input/i2c_seesaw.py` where the mapping is.

**All five controls now exist as hardware.** SELECT is the **SparkFun Qwiic Twist DEV-15083**,
ordered after the acceptance check below. RH1 can therefore attempt the complete touch-free journey
physically once the parts arrive.

**`APPROVED_FOR_RH1` is not a production encoder decision.** ADR 0026 § 7 remains the contract, and
the Twist is one prototype implementation of it.

The RH1 control assignment is therefore complete:

| Control | Hardware | Meaning |
|---|---|---|
| SELECT | SparkFun Qwiic Twist | rotate → focus/value · press → activate, confirm |
| PREVIOUS | Cherry MX, NeoKey socket 0 | previous item in content order |
| NEXT | Cherry MX, NeoKey socket 1 | next item in content order |
| — | NeoKey socket **2, deliberately empty** | tactile separation between NEXT and HOME |
| HOME | Cherry MX, NeoKey socket 3 | the way out; wakes and acts in one press |
| VOLUME | Adafruit 5880 | rotate → volume · press → play/pause |

Whether that spacing actually reads by hand is a physical measurement, not a layout claim.

### Qwiic Twist acceptance — `APPROVED_FOR_RH1`

Checked against ADR 0026 § 7 (AQENO Rotary Control Contract) and the real RH1 I²C build on
2026-08-19, from vendor documentation.

| Requirement | Verified result |
|---|---|
| Push function | Built-in momentary button ✓ |
| Incremental, detented | 24 detents per 360°, direction detected ✓ |
| Shaft | **6 mm**, takes any knob with a 6 mm knurled hole — matches § 7's 6 mm preference ✓ |
| Exchangeable caps | Any 6 mm knob; **no knob included** ✓ |
| I²C address | `0x3F`, jumper `0x3E`, software `0x08`–`0x77`; no conflict with `0x30`, `0x36`, `0x10`, `0x60` ✓ |
| Solderless | Qwiic/STEMMA QT, 2 connectors, no soldering ✓ |
| Supply | 3.3 V; 2.8 mA with LEDs off, 40.6 mA at 100 % ✓ |
| RGB to true off | Per-channel 0–255 PWM, so `(0,0,0)` is reachable — satisfies **DARK means zero visible light** ✓ |
| Runs on existing SHIM + hub | Yes, occupies one of the four downstream ports ✓ |
| Extra adapters needed | None ✓ |

**Not verifiable from documentation, so real-test items:** detent feel, rotational torque, push force
and whether a child or a person with reduced hand strength operates it comfortably (ADR 0026 § 7);
blind distinguishability from the VOLUME encoder (P22).

**Recorded limitation of the prototype.** ADR 0026 § 7 prefers SELECT and VOLUME to be the *same*
part with different caps. On RH1 they will be two different encoders — Twist and Adafruit 5880 — so
**RH1 cannot validate that preference**, and a blind-distinguishability result on RH1 is confounded:
two different encoders feel different regardless of their caps. Treat an RH1 pass as necessary, not
sufficient.

**Illumination caveat.** SparkFun's RGB LED sits on the board beneath the knob and the vendor
recommends a clear plastic knob so the light is visible. An opaque metal knob may block it entirely
— see § Encoder cap evaluation.

### Encoder cap evaluation — `REAL_TEST_REQUIRED`

Two aluminium knob types are now ordered, and both are `EVALUATION` samples rather than AQENO cap
decisions: the 32 mm knob with grub-screw fixing, and two 22.2 mm Elecrow illuminated-ring knobs
(CQA231128PB13). Judge them blind and with different hands, not by looks.

**Mechanical fit on the Twist is unverified.** Elecrow does not publish a bore diameter or shaft type
for the illuminated knob, so whether it seats on the Twist's 6 mm knurled shaft cannot be decided
from documentation. Test physically: seating, fixing, play, feel, grip, operation by a child, use
with reduced fine motor control, and blind findability.

**A functional concern is documented rather than assumed.** The Elecrow knob is sold *for RGB
encoders*, and Elecrow's own illuminated RGB encoder has a **transparent knurled shaft lit by an LED
inside the encoder**. The Twist has neither: it is an opaque shaft with one RGB LED on the PCB below.
A ring designed to be lit by a glowing shaft may therefore stay dark on a Twist. If it does, that
result says nothing about AQENO's illumination policy — it is a pairing mismatch to record and
discard for this combination. **A dark ring is not a failure criterion**, and nothing may be built to
force one to light.

Neither ordered knob is light-transmitting, so the *ergonomics* half of this evaluation is fully
covered by hardware already bought, while the *illumination* half depends on whether the Twist's LED
happens to reach the Elecrow ring. If it does not, a light-transmitting knob would be a purchasing
decision under the freeze, not a technical requirement — and nothing is recommended here.

What to record on the Twist besides fit: does light reach the ring, how evenly, the minimum visible
PWM step, disturbing residual brightness, light leaking into the enclosure, and **complete darkness
at `(0,0,0)`**.

## Target display and light direction

ADR 0025 records the direction: a compact panel of roughly 4–5 inches, high contrast, excellent
black level, controllable brightness, true pixel-off preferred, touch not required. AMOLED/OLED is
preferred and is explicitly not an architectural dependency — LCD/IPS, OLED, AMOLED and no display
at all must all stay modellable.

No separate status or RGB LED is planned for the target device; the display carries status. RH1's
existing illumination remains prototype hardware behind the `StatusLeds` port, and no code may
assume user-facing light exists.

The intended later computer is a low-cost Linux SBC of roughly Raspberry Pi Zero 2 W class. That is
a direction, not a decision: **PySide6/QML performance on that class is unverified and is a real
risk to ADR 0002** (`ROADMAP.md` P2). No board, panel or SoC choice is wired into Core.

For a later internally pre-assembled carrier PCB, soldered components are acceptable. "No soldering
required" remains the rule for RH1 and for anything an end user assembles. The durable requirement
is ADR/P18 repairability: a defective standard module should be replaceable without discarding the
device.

## Feedback channels

AQENO may acknowledge an intention through audio, display, LED or physical affordance. The adapter
implements concrete hardware output; application/presentation policy determines whether feedback is
appropriate. Domain logic does not select a QML animation, NeoPixel colour or board-specific effect.

The encoder and key LEDs are semantic indicators, not decoration. They must support true off and
must obey Night/Dark-Room policy. Continuous animation or illumination solely to attract attention
is out of scope. Diagnostic LEDs that cannot be disabled in software must be hidden by the enclosure.

The future `Send to AQENO` concept illustrates the boundary without requiring implementation: RH1
might present a message as a heart on the display, while another device could use an illuminated
large button, an LED symbol or audio. The underlying application capability need not change.

## Open components

Not yet selected or acquired:

- NFC reader and tags;
- final enclosure-side NFC antenna and object area;
- final mains/mobile power arrangement;
- final enclosure and mechanical fixtures;
- any additional sensor or actuator justified by later product work.

The SELECT encoder is no longer open: the Qwiic Twist is accepted and ordered. The VCNL4040 is
accepted but **deferred and unordered**, which is the distinction this document exists to keep —
`APPROVED_FOR_RH1` describes suitability, never procurement, and never production.

Possession status for everything above is in `INVENTORY.md`, not here.

NFC remains simulated until the current Vertical Slice works. PN532 is still a candidate technology
family, but a specific board requires a feasibility check for Linux support, I2C compatibility,
read range, mounting behind the enclosure and genuinely solderless installation.

### Sensing: ambient light and proximity

The **Adafruit VEML7700 (PID 4162, STEMMA QT/Qwiic) has been ordered** for RH1. It measures ambient
light only. A feasibility check must still confirm its Linux/I²C path, address coexistence on the
shared bus, useful placement away from panel spill and whether its readings produce calmer behaviour
in real use. Raw lux belongs to the sensor adapter; display policy interprets it. No generic
adaptive-brightness engine is implied.

The **Adafruit VCNL4040 (PID 4161)** — ambient light *and* IR proximity over I²C on a STEMMA QT
breakout — is the current **target candidate**, because ADR 0026 § 10 wants near-hand proximity for
one purpose: temporarily illuminating the relevant controls in a dark room. It would functionally
replace the VEML7700, and a later AQENO reference device most likely needs one sensor rather than
both.

#### VCNL4040 acceptance — `APPROVED_FOR_RH1`

Checked on 2026-08-19 against ADR 0026 § 10 and the real RH1 build, from vendor documentation.

| Requirement | Verified result |
|---|---|
| I²C address / bus conflict | `0x60`; distinct from `0x30`, `0x36`, `0x3F` and `0x10` — no conflict ✓ |
| Runs on the existing hub | Yes, two STEMMA QT connectors; occupies one downstream port ✓ |
| Soldering | None required ✓ |
| Extra hardware for the open RH1 test | None — the sensor runs bare or behind a defined test opening ✓ |
| Ambient light **and** proximity under Linux | Both exposed: proximity 0–200 mm, light 0.0125–6553 lux, via the CircuitPython driver on the Blinka path RH1 already uses ✓ |
| VEML7700 in parallel for comparison | Yes — `0x10` and `0x60` coexist; needs the daisy-chain hop in § Qwiic capacity ✓ |

`APPROVED_FOR_RH1` covers the prototype only. It is not a production sensor decision, and it is not
a claim that the VCNL4040's ambient-light quality suffices — that is the measurement the retained
VEML7700 exists for.

**Procurement is deferred: the VCNL4040 is unavailable and deliberately not ordered**
(`INVENTORY.md`). Acceptance and procurement are separate decisions, and this is what that
separation looks like in practice.

#### What that means for RH1 today

| Capability | RH1 now | Later |
|---|---|---|
| Ambient light | **VEML7700** — the real working sensor, not a placeholder | VEML7700 or VCNL4040, decided by measurement |
| Proximity | **does not exist** | VCNL4040, if the comparison supports it |

Proximity is **not simulated to make the feature look present**. AQENO must work completely without
it: it is a comfort capability for temporary orientation in the dark, never a precondition for
operation. `DARK means zero visible light` stays fully testable without it. The one thing that
cannot be validated yet is "hand approaches → controls illuminate temporarily".

Not yet done, and deliberately not now: the CircuitPython VCNL4040 driver is not in the `rh1`
optional dependencies and no `Proximity` port, adapter or illumination policy exists. Nothing is
implemented for hardware that has not arrived.

#### The sensor swap is already a one-adapter change

Verified against the code on 2026-08-19, so the later migration is not a surprise:

- `ports/ambient_light.py` defines `AmbientLight` as a single `read_lux()` — no sensor, register or
  bus detail crosses it;
- `adapters/ambient_light/veml7700.py` implements it against an injected register bus, so it owns
  the Vishay specifics and nothing above it does;
- `DisplayService` takes `ambient_light: AmbientLight | None`; `None` is the honest representation of
  an absent sensor and is handled without a branch anywhere in Domain.

A VCNL4040 therefore arrives as **one more adapter behind the same port**, and proximity — when it
exists — becomes its own port beside it. **No capability framework is created for this** (ADR 0017
§ 1, ADR 0026 § 12), and no Display, Night or UI domain logic changes.

**No optical cover is to be bought** (ADR 0026 § 10). RH1 tests the sensor bare or behind a defined
opening first; front material, window size, sensor distance, internal reflection, crosstalk, range,
false positives, full darkness and direct sunlight are measured before any material is specified.

"Most likely" is not evidence, and the following is deliberate:

- RH1 **keeps** its VEML7700 as the reference against which a VCNL4040's ambient-light quality is
  measured — especially at very low room brightness, where the dimming and illumination decisions
  actually matter.
- **No claim that the VCNL4040 suffices may be made before that comparison exists.** The VEML7700
  must equally not be carried forward as a mandatory second production component by default.
- Mounting behind real front material must be validated physically: IR transmission, internal
  reflection, crosstalk and real detection range are not assumed from a datasheet.
- Proximity is presence awareness and illumination assistance only — never gesture control. Sensor
  failure must leave every control fully usable and must produce no error surface.
- A product may use the bare sensor or another compatible solution on its own carrier. Neither part
  is a mandatory production component, and **neither is bought now**.

No `Proximity` port, adapter or illumination policy exists, because no AQENO hardware reports
proximity.

### Transitional tag reader — EM4100 USB RFID

RH1 has an **owned USB RFID reader of the 125 kHz EM4100/EM4102 class**. Its exact model is not yet
verified.

> **It is `TRANSITIONAL`, not AQENO's NFC solution, and not 13.56 MHz.**

It exists so the tag interaction chain can be built now without any purchase:

```text
tag presented → tag identifier → AQENO-local assignment → semantic action
```

Domain and Application must remain independent of it. The semantic boundary is the existing tag
input event carrying an identifier — no EM4100 packet, no reader protocol and no NFC UID detail
belongs above the adapter. A future PN532, PN7160 or any other reader replaces the adapter and
nothing else.

**No adapter is written before the physical device is identified.** On first connection record
`lsusb`, and depending on what it reports, `/dev/input/by-id`, `/dev/serial/by-id` and the kernel
log. Cheap readers of this class often present as a USB HID keyboard that simply types an identifier
followed by Enter; others expose a serial device. Which one this is decides the adapter, and
guessing it would be inventing hardware behaviour.

`NFC_REFERENCE_CANDIDATE.md` holds the future 13.56 MHz decision, which remains open and unbought.

### NFC object area

The reader is unselected, but the physical requirement is decided (ADR 0026 § 11):

> **Place, do not aim.**

- a **generous, flat object area** with **no recess and no well** — standing figures work, simple
  3D-printed objects need no AQENO-specific under-geometry, flat cards work equally;
- error-tolerant, and findable by touch where that is possible without intrusive geometry: a slight
  material or texture difference, or a constructional seam, may be evaluated;
- the enclosure reserves adequate area from the start; the antenna solution is a later measurement
  and is not implied here;
- **magnetic positioning** may be added later as an option — NFC identifies, magnetism may position
  and hold. Never a precondition for NFC, never mandatory proprietary geometry, ordinary cards and
  tags must keep working, and the interaction with the antenna, speakers, display and remaining
  electronics must be measured. No magnet arrangement is specified.

### Hardware capability matrix

Documentation, **not** a runtime registry, DSL or plugin mechanism (ADR 0026 § 12; ADR 0010,
ADR 0017 § 1 and ADR 0024 § 5 each rejected a framework). Where code needs to know whether hardware
exists, the existing ports already report it.

| Capability | RH1 today | Possible reference hardware | Notes |
|---|---|---|---|
| Controls (SELECT, PREVIOUS, NEXT, VOLUME, HOME) | 4 of 5; SELECT missing | **required** | Not a capability — it is the interaction contract itself |
| `DISPLAY` | yes, 7" DSI | optional, preferred compact 4–5" | ADR 0017: display is a capability, not a dependency |
| `TOUCH` | yes | optional | Never required for any path (ADR 0024 § 1) |
| `NFC` | no — 125 kHz EM4100 reader stands in, `TRANSITIONAL` | optional | Shortcut, never an access requirement |
| `AMBIENT_LIGHT` | VEML7700, the working sensor | optional | Possibly merged into VCNL4040 later |
| `PROXIMITY` | no — VCNL4040 deferred | optional | Illumination assistance only; unimplemented, never simulated |
| `CONTROL_ILLUMINATION` | yes, NeoPixel | optional | Never a precondition for operation (P24) |
| `BATTERY` | no | optional | USB-C power; commodity power bank untested |

A capability with no hardware has **no UI surface** (P15) and no branch in Domain or Application.

The Waveshare 5-inch HDMI AMOLED is a possible **RH2** display candidate for later evaluation. This
records an experiment option only: it is not a hardware decision, does not replace the acquired RH1
touch display and creates no current adapter or purchasing requirement.

The MiniAmp and speakers are selected, but acquisition is not integration evidence. Before the audio
path is accepted, boot with the Qwiic SHIM and MiniAmp installed, verify the stable ALSA card,
left/right/stereo output, rotary volume and play/pause, Qwiic controls, touch, reboot and offline local
playback. Record clean startup/shutdown, usable gain, sustained thermal/power behaviour and measured
sound pressure. Until then, USB or HDMI audio remains acceptable for software work.

## Known prototype constraints

- Qwiic simplifies prototype wiring but is not an AQENO platform requirement.
- Shared I2C wiring still requires address, bus-load, cable-length and startup-order validation.
- The FREENOVE panel's exact revision and display-server behaviour are not yet recorded;
  authoritative panel off and touch routing therefore remain unproven despite the known MIPI DSI
  connection and published display characteristics.
- The NeoKey and encoder boards are development modules, not production control assemblies.
- Small board LEDs may need physical shielding; software-off capability must be verified on the
  assembled hardware.
- The touch display makes RH1 useful for Device UI work, but screenless core operation remains a
  product boundary and must be protected by physical-input/display-off tests.
- The current control placement, key order, switch feel and enclosure ergonomics require user
  testing. The NeoKey socket assignment (PREVIOUS 0, NEXT 1, gap 2, HOME 3) is a provisional layout
  decision that has not been felt by hand.
- Blind findability, tactile distinguishability of SELECT and VOLUME caps, and whether HOME can be
  pressed accidentally are unmeasured (P21, P22).
- Logical volume limits are not hearing-safety claims until the complete amplifier/speaker path is
  measured and calibrated as specified in `CONFIGURATION_DEFAULTS.md`.
- The MiniAmp's advertised rating and the speakers' nominal ratings do not establish safe,
  distortion-free or thermally sustainable output in the assembled enclosure.
- Raspberry Pi boot time and power behaviour must be measured on the assembled unit rather than
  inferred from desktop tests.

## Mechanical and power requirements

RH1 remains the acquired prototype described above; the repairability principles in
`PRODUCT_FOUNDATION.md` do not change its components or define an enclosure. Its use of a Raspberry
Pi, Qwiic/STEMMA QT connections, standard switches and separable development modules is appropriate
for experimentation, access and replacement even if a later cost-optimised device integrates some
functions.

As RH1 is assembled, record the exact installed component/revision, relevant electrical
characteristics and connection method when they become known. Unknown inventory details remain
unknown rather than guessed. This is the first step toward identifiable hardware, not a request for
a service manual or compatible-parts catalogue now.

- Boards are fixed to printed bosses or standoffs; no breadboard or loose Dupont wiring is a
  permanent enclosure component.
- Buttons are supported by the front plate rather than relying on PCB sockets to absorb user force.
- Cables receive strain relief and internal connectors remain serviceable.
- Exposed PCBs and unavoidable diagnostic light are hidden from the user.
- Service-relevant electronics should use suitable removable fasteners or connections where
  practical. Adhesive is not prohibited where it does not make a realistic repair needlessly
  destructive.
- Reference input is standard USB-C. A commodity power bank may be used only after sustained load,
  idle-load, wake/restart and full-system capacity have been tested.

## Current architecture fit

The existing boundaries are sufficient for RH1:

- `ports/input.py` defines semantic input events and the synchronous `InputBus` from ADR 0011;
- the keyboard adapter and fake input bus already prove that concrete inputs are replaceable;
- playback consumes semantic volume, transport and NFC intentions without hardware imports;
- display state is independent from playback, so physical controls remain meaningful while visual
  output is off;
- ADR 0010 keeps GPIO, I2C, display power, LEDs and NFC implementations in adapters;
- ADR 0012 keeps QML/PySide6 outside the Core.

The RH1 controls adapter now emits logical controls and the local mapping layer supplies product
actions, pending on-device I2C validation. The display and selected audio path still need verified
platform integration; selection or acquisition alone does not justify concrete adapter behaviour.
This does not need a universal action bus, dynamic input engine, persona-specific hardware profiles
or adapters for hypothetical external switches.
