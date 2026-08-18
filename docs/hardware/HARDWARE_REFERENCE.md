# AQENO Reference Hardware 1

**Identifier:** AQENO Reference Hardware 1 (`RH1`)

**Status:** Prototype platform; controls adapter implemented, pending on-device validation; MiniAmp
selected as RH1 audio, physical receipt/integration evidence still to record

**Date:** 2026-08-18

## Role

Reference Hardware 1 is the first concrete platform on which AQENO is developed, measured and
tested. AQENO should work exceptionally well on it. It is not the definition of AQENO and does not
make Raspberry Pi 4, a 7-inch touchscreen, Qwiic, one encoder, four MX switches or this control
mapping permanent Core requirements.

> Reference Hardware proves AQENO. It does not define AQENO.

Since ADR 0024 that statement is binding for the controls as well: the Cherry MX keys, the single
Qwiic encoder and the touch panel are **prototype input hardware**. They do not describe the target
product layout, and the software is developed against the target vocabulary (NAV, VOL, transport
rocker) rather than against what happens to be plugged in.

Future hardware may omit the screen, use different controls or provide a more display-oriented
experience. Domain and application code consume user intentions and product state; adapters own
boards, buses, addresses, pins and physical mappings. No generic hardware-profile or persona system
is implied.

## RH1 components

| Component | Quantity | Product identifier | Role |
|---|---:|---|---|
| Raspberry Pi 4B | 1 | Raspberry Pi 4 Model B | Reference computer |
| 7-inch touchscreen | 1 | FREENOVE; 800 x 480, 60 Hz, capacitive 5-point touch, MIPI DSI; exact SKU/revision to record from the unit | Device UI and touch input |
| I2C STEMMA QT rotary encoder | 1 | Adafruit 5880 | Relative volume, press for play/pause, restrained RGB feedback |
| NeoKey 1x4 QT | 1 | Adafruit 4980 | Up to four physical MX keys with individually controlled NeoPixels |
| CHERRY MX2A Brown RGB, 3-pin | several | CHERRY MX2A-G1NA | Quiet tactile switches |
| Transparent Cherry MX keycaps | 1 pack of 10 | Adafruit 4956 | Light-transmitting keycaps |
| Qwiic SHIM for Raspberry Pi | 1 | SparkFun DEV-15794 | Solderless Raspberry Pi I2C/Qwiic connection |
| STEMMA QT/Qwiic hub | 1 | Adafruit 5625 | Central I2C distribution and free branches |
| 300 mm STEMMA QT/Qwiic cable | 3 | Adafruit 5384 | Solderless JST-SH wiring |
| Stereo I2S amplifier | 1 | HiFiBerry MiniAmp | 2 x 3 W RH1 audio output; preassembled 40-pin module |
| Mini speaker, 3 W / 4 ohm | 2 | QUARKZMAN, 44 x 31 x 15 mm | Left/right prototype speakers |
| Speaker lead and connector | 2 | JST-PH 2.0, 100 mm; supplied with speakers | Removable speaker connection |

The display's exact SKU/revision and the Raspberry Pi's RAM variant should be added when confirmed
from the physical units. Its reported 800 x 480 resolution, 60 Hz refresh, capacitive 5-point touch
and MIPI DSI connection are the RH1 design target; they do not establish authoritative panel-off or
Linux touch/display-server behaviour. The MiniAmp uses the kernel-supported `hifiberry-dac` overlay;
its actual ALSA presentation, channel arrangement and safe acoustic range still require RH1
validation. Unknown inventory details must not be guessed.

Most components above are on hand from the prototype inventory. The MiniAmp is the selected audio
reference; receipt and exact board revision are not claimed until recorded from the unit.

No NFC reader has been acquired. `NFC_REFERENCE_CANDIDATE.md` records the PN532/SPI spike candidate;
it is not part of RH1 until that spike passes.

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
        │   ├── key 1 → Previous
        │   ├── key 2 → unassigned reserve
        │   ├── key 3 → Next
        │   └── key 4 → unassigned reserve
        │
        ├── free branch → unused; PN532 candidate is SPI, not I2C
        └── free branch → future hardware if a real use case requires it
```

The Qwiic SHIM is the thin, HAT-stackable DEV-15794. It carries the Pi I2C bus and power beside the
MiniAmp; it does not consume any of the MiniAmp's I2S/control GPIOs.

## RH1 resource map

| Resource | Physical pins/interface | Owner(s) | State |
|---|---|---|---|
| MIPI DSI | dedicated DSI connector | FREENOVE display | exclusive, no GPIO-header conflict |
| I2C1 SDA/SCL | GPIO2/3, pins 3/5 | Qwiic SHIM → 5880 (`0x36`) + NeoKey (`0x30`) | shared bus; addresses distinct |
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
| Encoder counter-clockwise/clockwise | `primary_encoder.rotate_left` / `.rotate_right` | Volume down/up |
| Encoder short press | `primary_encoder.short_press` | Play/Pause |
| Encoder long press (≥800 ms) | `primary_encoder.long_press` | unassigned; long press is setup/service only (ADR 0024 § A2) |
| NeoKey LEFT short press | `primary_left.short_press` | back — currently resolved as Previous |
| NeoKey RIGHT short press | `primary_right.short_press` | forward — currently resolved as Next |
| Touch | presentation intention / `WakeRequest` as applicable | Contextual Device UI interaction |
| Future NFC reader presents/removes UID | `NfcPresented` / `NfcRemoved` | Resolve an AQENO-local token assignment |

The hardware adapter ends at logical input events. The persistent AQENO mapping layer then emits
semantic application intentions. Core code never receives “Cherry key 3”, a GPIO number, Qwiic
address or NeoKey coordinate. The Adafruit 5880 adapter owns its official seesaw details: default
address `0x36`, push button pin 24 and NeoPixel pin 6. It normalizes the board's reported direction
before anything above the adapter sees left/right.

`PrimaryAction` and `Acknowledge` are plausible future intentions but are not Vertical Slice events.
They must not be added merely to occupy reserve keys or anticipate alternative hardware.

## Target control direction

Recorded so software and UI can be built against it. **This is not a purchase list and not a
component decision.**

| Control | Role | Semantics |
|---|---|---|
| NAV rotary encoder with press | navigation | rotate: move focus; short press: activate / confirm |
| VOL rotary encoder with press | volume and playback | rotate: volume; short press: play/pause — permanently, never contextual |
| LEFT | back | context-resolved: previous level, or previous section during linear playback |
| RIGHT | forward | context-resolved: forward level where meaningful, or next section |

No separate OK button. No long press or double press in everyday operation (ADR 0024 § A2). LEFT and
RIGHT may become one quality momentary centre-off rocker on the target device; that is a
construction change, not a semantic one.

Controls must also feel right, not only work: an encoder with clearly felt detents, a switch or
rocker with a defined actuation point. Inherent physical feedback is preferred over invented cues
(`PRODUCT_FOUNDATION.md` P20), and AQENO does not emit a sound for every physical action.

Quality expectations, without fixing parts: the target device does not use controls that feel like
maker components. High-grade encoders of the Bourns PEC11R or Alps Alpine EC11 class are plausible
candidates, and NAV and VOL should ideally be the **same** electrical and mechanical encoder type,
with different knobs supplying different haptics — fewer spare-part variants, simpler procurement,
simpler carrier PCB, easier repair. The rocker must be a quality momentary centre-off part, never a
latching mains-style switch.

Ergonomics: controls belong on the top surface or an angled upper face, not on a vertical front that
pushes the device backwards when pressed. Pressure should act towards the standing surface. The
front stays visually calm and belongs to the display. Enclosure design is explicitly out of scope
here; only the requirement is recorded.

### RH1 control plan

The product-shaped RH1 test layout is:

```text
[ Cherry MX LEFT ]   [ NAV encoder ]   [ Cherry MX RIGHT ]   [ VOL encoder ]
```

No middle OK switch is required. The acquired Adafruit 5880 takes the VOL/Play role; NAV needs a
second suitable encoder, which is simulated until that hardware exists. **No purchase and no
component decision follows from this plan** — the address-jumper question on a second 5880 must be
checked against Adafruit's documentation first, because bridging solder jumpers would collide with
the no-solder acceptance gate below.

Until NAV exists on the box, RH1 cannot demonstrate the touch-free journey physically, and the
physical path from Now Playing back to Home stays touch-only (ADR 0024 § A3).

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
- VEML7700 ambient-light sensor; candidate for measuring lux during glanceable-display experiments;
- final mains/mobile power arrangement;
- final enclosure and mechanical fixtures;
- any additional sensor or actuator justified by later product work.

NFC remains simulated until the current Vertical Slice works. PN532 is still a candidate technology
family, but a specific board requires a feasibility check for Linux support, I2C compatibility,
read range, mounting behind the enclosure and genuinely solderless installation.

The VEML7700 is an RH1 candidate, not yet selected hardware. A feasibility check must confirm its
Linux/I²C path, address coexistence on the shared bus, useful placement away from panel spill and
whether its readings produce calmer behaviour in real use. Raw lux belongs to the sensor adapter;
display policy interprets it. No generic adaptive-brightness engine is implied.

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
- The current control placement, key order, switch feel and enclosure ergonomics require user testing.
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
