# RH1 commissioning and validation checklist

Record results and measurements in `docs/product/USE_OBSERVATIONS.md`; do not mark an item complete
from desktop simulation alone. What hardware exists and what it is for is in `INVENTORY.md`.

## Hardware smoke test — run this first, before any further implementation

When the ordered parts arrive, do not start building features. Work these seven phases in order;
each one can fail in a way that makes the next meaningless.

**Phase 1 — I²C.** SHIM, hub, NeoKey, 5880, Twist and VEML7700 are all detected **simultaneously**,
at `0x30`, `0x36`, `0x3F` and `0x10`, with no bus errors and no dropouts under sustained polling.

**Phase 2 — controls.** Each event individually: PREVIOUS, NEXT, HOME, SELECT rotate, SELECT press,
VOLUME rotate, VOLUME press.

**Phase 3 — blind.** Without looking at the device: find HOME · tell PREVIOUS and NEXT apart · find
SELECT · find VOLUME · change volume · pause · reach Home · operate a menu.

**Phase 4 — mechanics.** One-handed operation; does the device slide? Knob torque, switch force,
accidental inputs, and whether the empty NeoKey socket between NEXT and HOME actually separates them
by feel.

**Phase 5 — knobs.** 32 mm against 22.2 mm, judged blind and with different hands — not by looks.

**Phase 6 — light.** Twist RGB verified at `(0,0,0)`, NeoPixels at 0, display off; hunt for any
remaining stray LED; check the VEML7700 in a genuinely dark room.

**Phase 7 — tag reader.** Identify the owned USB RFID device physically (`lsusb`, then
`/dev/input/by-id`, `/dev/serial/by-id` or the kernel log as applicable) **before** any adapter is
written.

## Installation and boot

- clean Raspberry Pi OS image; I²C, SPI and I²S deliberately enabled;
- AQENO installed at `/opt/aqeno`, systemd and Avahi units installed;
- once the canonical logo and real DSI path are available, install the Plymouth theme and verify cold
  boot shows only the dark AQENO visual—no Pi rainbow, desktop, taskbar, cursor, terminal or window
  decoration;
- physical controls become responsive, then playback, then Device UI; record each timestamp;
- record power-on → first AQENO visual, UI process, first QML frame, Core ready and locally usable;
- verify first frame dismisses Plymouth immediately with no fixed delay, black gap or mode switch;
- test the documented debug boot by restoring visible boot detail; headless boot must not require
  Plymouth;
- `http://aqeno.local` opens Admin without an IP address or port;
- initial ownership and password recovery require Previous → Encoder → Next at the device;
- Admin UI and `/api/v1` share port 80/origin; direct IP port 80 works only as recovery;
- port 8766 listens only on loopback and is not reachable from another LAN host;
- mDNS recovers after interface reconnect and DHCP address changes;
- API or network failure does not stop local playback.

## Controls and light

- verify the PREVIOUS / NEXT / HOME MX defaults on NeoKey sockets 0, 1 and 3; confirm socket 2 stays
  silent; change one allowed mapping, reboot, then restore defaults;
- encoder rotation changes volume, short press toggles Play/Pause, and long press never also emits
  short press;
- **HOME reaches Home from every surface, never stops playback, and wakes *and* acts on one press**
  (ADR 0026 § 4);
- bounce, rapid input and simultaneous presses are harmless;
- encoder/NeoKey feedback is restrained, semantic and completely off in Bedtime;
- controls retain meaning while the display is OFF and do not wake it routinely.

## Touch-free operation (ADR 0024)

Run the everyday journey with touch disabled or ignored. Administration is explicitly not part of
this test.

- start AQENO, reach a usable profile context, open the library, choose a category where one
  exists, choose a medium, start playback;
- pause, resume, change volume, use previous/next, navigate back, return to playback;
- later, when they exist: choose radio, choose a podcast, set and start a timer, cancel a timer;
- verify no step required a touch, and that the input which woke the display did not also select
  anything;
- verify that no step needed a long press or a double press (ADR 0024 § A2);
- **unblocked once the parts arrive:** all five controls now exist as hardware — SELECT is the
  Qwiic Twist, PREVIOUS/NEXT/HOME are Cherry MX switches on NeoKey sockets 0, 1 and 3. The complete
  journey can be attempted physically for the first time.

## Blind operation and tactile identity (ADR 0026 § 1)

Run each item with the eyes closed or the device out of sight, in a fully dark room.

- every control is found by hand without light and without labels;
- SELECT and VOLUME are told apart by hand alone, with the chosen caps;
- HOME's position and shape are found blind and are **not** pressed by accident;
- PREVIOUS and NEXT read as one adjacent pair, distinct from HOME;
- rotation direction, detent feel and push force are usable by the actual child and by an adult with
  reduced hand strength;
- an ordinary one-handed press does not appreciably move the device on a normal surface
  (ADR 0026 § 6) — test with and without feet, and with the controls on an inclined face if used.

## Night, darkness and illumination (ADR 0026 § 9)

- **DARK reaches zero visible light:** display, control LEDs, status LEDs, HOME key and every
  unavoidable operating indicator. Verify in a fully dark room after the eyes have adapted, not by
  glancing at it in a lit room;
- determine the **minimum illumination level that is still not disturbing** in that room, and
  whether any level is useful at all;
- confirm the `off` night preference behaves exactly as the previous unconditional rule did.

## Sensing (ADR 0026 § 10)

- record VEML7700 lux behaviour at very low room brightness, away from panel spill and away from
  control-LED spill; it is RH1's working ambient sensor, so brightness thresholds, dark/night
  behaviour and real bedroom transitions are testable now;
- verify that removing the sensor leaves every control fully usable with no error surface;
- verify AQENO is complete **without proximity**, which RH1 does not have: `DARK means zero visible
  light` must be fully demonstrable, and only "hand approaches → controls illuminate" stays untested;
- **deferred until a VCNL4040 exists:** run both sensors in parallel (`0x10` and `0x60`) and compare
  very low lux, dark bedroom, both brightness transitions, stability, response speed, display and
  LED stray light, and suitability for automatic display brightness. Only then decide whether the
  VCNL4040 takes over ambient as well, the VEML7700 keeps ambient while the VCNL4040 supplies
  proximity, or a later product solution replaces both;
- measure proximity range and the false-positive rate when someone walks past or turns over in bed;
- validate any sensor behind the real front material: IR transmission, internal reflection and
  crosstalk.

## NFC object area (ADR 0026 § 11)

- the object area is flat with **no recess**, and works with standing figures, simple 3D-printed
  objects and flat cards alike;
- read reliability across the whole area, not only at its centre — "place, do not aim";
- whether the area is findable by touch without intrusive geometry;
- any magnet experiment is measured against the antenna, speakers, display and remaining
  electronics before it is called an option.

## Display and touch

- actual output is 800×480 at 60 Hz, touch targets remain reliable at edges;
- focus states are unmistakable from normal seated viewing distance, not only close up;
- INTERACTIVE, DIM, OFF, SETUP and permitted AMBIENT transitions follow policy;
- playback continues in OFF; routine metadata/playback events do not wake the display;
- Dark Room reaches fully black display and LEDs; wake and return paths have no dead ends.
- **Rendering cost is measured, not argued.** The premium visual language is built entirely from cheap
  primitives — no blur, drop shadow, shader, offscreen layer or particle system — and the argument that
  it is affordable is structural, not measured: the offscreen grab path used for screenshots reports no
  scene-graph timings. On RH1, measure encoder-to-focus response, focus movement and the artwork
  ambience under continuous rotation, and confirm the two MODERATE effects (the layered artwork glow
  and the progress ring's bloom arc) hold frame rate. If either does not, its cost class was wrong.
- The first cover shown after boot must not stall the surface while its ambient colour is obtained.

## Audio

- verify `sndrpihifiberry` detection and I²S left/right/stereo output through the MiniAmp and both
  4 Ω speakers;
- verify the Qwiic SHIM, 5880 and NeoKey in parallel with MiniAmp GPIO16/18-21/26 reserved;
- measure useful volume range, distortion, idle noise and startup/shutdown transients;
- calibrate child/night/headphone ceilings rather than treating logical values as dB;
- verify pause/resume, chapter boundaries, long playback and recovery after source loss.

## NFC candidate

- the reader on RH1 is the owned 125 kHz EM4100 USB device, `TRANSITIONAL` and **not** NFC: identify
  it physically (Phase 7) before writing any adapter;
- prove the semantic chain is hardware-independent — tag identifier in, AQENO assignment out — so a
  future 13.56 MHz reader replaces only the adapter;
- `NFC_REFERENCE_CANDIDATE.md` is deferred; no NFC hardware is bought or validated yet;
- unassigned token is calm and non-destructive;
- assigned token launches through the active profile's effective access policy;
- management capture never launches an existing assignment and cancellation restores playback;
- removal/re-presentation, rapid repeats and reader disconnect/reconnect are deterministic.

## Resilience

- power loss during playback preserves the last safe resume checkpoint;
- power loss during media upload/import leaves no partial visible media object;
- unavailable NAS mount preserves index, metadata, assignments and local playback;
- service restart and repeated boot do not duplicate media or regenerate device identity/key;
- diagnostics identify failed display, input, NFC, audio and storage boundaries in AQENO terms.
