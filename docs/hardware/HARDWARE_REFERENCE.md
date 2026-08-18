# AQENO Reference Hardware 1

**Identifier:** AQENO Reference Hardware 1 (`RH1`)

**Status:** Acquired prototype platform; controls adapter implemented, pending on-device validation;
display and audio hardware acquired, integration unverified

**Date:** 2026-08-18

## Role

Reference Hardware 1 is the first concrete platform on which AQENO is developed, measured and
tested. AQENO should work exceptionally well on it. It is not the definition of AQENO and does not
make Raspberry Pi 4, a 7-inch touchscreen, Qwiic, one encoder, four MX switches or this control
mapping permanent Core requirements.

> Reference Hardware proves AQENO. It does not define AQENO.

Future hardware may omit the screen, use different controls or provide a more display-oriented
experience. Domain and application code consume user intentions and product state; adapters own
boards, buses, addresses, pins and physical mappings. No generic hardware-profile or persona system
is implied.

## Acquired components

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
| Stereo I2S Class-D amplifier | 1 | Soldered MAX98357, 3 W; product 333355 | Final prototype audio amplifier with screw terminals |
| Mini speaker, 3 W / 4 ohm | 2 | QUARKZMAN, 44 x 31 x 15 mm | Left/right prototype speakers |
| Speaker lead and connector | 2 | JST-PH 2.0, 100 mm; supplied with speakers | Removable speaker connection |

The display's exact SKU/revision and the Raspberry Pi's RAM variant should be added when confirmed
from the physical units. Its reported 800 x 480 resolution, 60 Hz refresh, capacitive 5-point touch
and MIPI DSI connection are the RH1 design target; they do not establish authoritative panel-off or
Linux touch/display-server behaviour. The amplifier's exact Linux/I2S presentation and stereo
channel arrangement must be verified from the unit and vendor documentation before an adapter or
wiring contract is recorded. Unknown inventory details must not be guessed.

No NFC reader has been acquired. `NFC_REFERENCE_CANDIDATE.md` records the PN532/SPI spike candidate;
it is not part of RH1 until that spike passes.

## Prototype topology

```text
Raspberry Pi 4B
│
├── 7-inch Touch Display
│
├── Soldered Stereo I2S MAX98357 amplifier
│   ├── QUARKZMAN 3 W / 4 ohm speaker (left)
│   └── QUARKZMAN 3 W / 4 ohm speaker (right)
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

The hub creates physical connection capacity, not product scope. Reserved keys and free branches
remain unused until a tested interaction needs them.

## Reference interaction mapping

| Physical event | Adapter output | Product meaning |
|---|---|---|
| Encoder clockwise/counter-clockwise | `VolumeDelta(delta)` | Relative volume change |
| Encoder press | `TogglePlayback` | Play or pause according to current playback state |
| NeoKey Previous | `Previous` | Contextual previous/rewind behaviour decided above the adapter |
| NeoKey Next | `Next` | Contextual next/skip behaviour decided above the adapter |
| Touch | presentation intention / `WakeRequest` as applicable | Contextual Device UI interaction |
| Future NFC reader presents/removes UID | `NfcPresented` / `NfcRemoved` | Resolve an AQENO-local token assignment |

The mapping ends at semantic events. Core code never receives “Cherry key 3”, a GPIO number, Qwiic
address or NeoKey coordinate. `Previous` and `Next` semantics depend on content context and remain an
application/domain decision.

`PrimaryAction` and `Acknowledge` are plausible future intentions but are not Vertical Slice events.
They must not be added merely to occupy reserve keys or anticipate alternative hardware.

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

The amplifier and speakers are acquired, but acquisition is not integration evidence. Before the
audio path is accepted, record the Pi connection, required Linux configuration, actual left/right
behaviour, clean startup/shutdown, usable gain range, sustained thermal/power behaviour and measured
sound pressure. Until then, an already available USB or HDMI audio output remains acceptable for
software work. The final audio path must not consume or electrically conflict with the practical
connection path for Reference controls.

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
- The MAX98357 board's advertised rating and the speakers' nominal ratings do not establish safe,
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

The RH1 controls adapter now maps the acquired encoder and NeoKey through this boundary, pending
on-device I2C validation. The display, amplifier and speakers are acquired but still need verified
platform integration; acquisition alone does not justify concrete adapter behaviour. This does not
need a universal action bus, dynamic input engine, persona-specific hardware profiles or adapters
for hypothetical external switches.
