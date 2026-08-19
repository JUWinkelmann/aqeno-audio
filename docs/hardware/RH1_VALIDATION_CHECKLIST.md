# RH1 commissioning and validation checklist

Record results and measurements in `docs/product/USE_OBSERVATIONS.md`; do not mark an item complete
from desktop simulation alone.

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
- **partly blocked physically:** the RH1 control plan is SELECT · PREVIOUS · NEXT · VOLUME · HOME,
  and no SELECT encoder exists yet. Focus movement and activation therefore still run on the desktop
  simulator only. Returning from Now Playing to Home is **no longer blocked** — HOME runs on
  hardware already present. Recorded rather than worked around.

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

- record VEML7700 lux behaviour at very low room brightness, away from panel spill;
- **only after that:** compare a VCNL4040's ambient-light readings against it before any claim that
  one sensor suffices;
- measure proximity detection range, and the false-positive rate when someone walks past or turns
  over in bed;
- validate any sensor behind the real front material: IR transmission, internal reflection and
  crosstalk;
- verify that removing the sensor leaves every control fully usable with no error surface.

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

## Audio

- verify `sndrpihifiberry` detection and I²S left/right/stereo output through the MiniAmp and both
  4 Ω speakers;
- verify the Qwiic SHIM, 5880 and NeoKey in parallel with MiniAmp GPIO16/18-21/26 reserved;
- measure useful volume range, distortion, idle noise and startup/shutdown transients;
- calibrate child/night/headphone ceilings rather than treating logical values as dB;
- verify pause/resume, chapter boundaries, long playback and recovery after source loss.

## NFC candidate

- complete `NFC_REFERENCE_CANDIDATE.md` spike before calling NFC Reference-supported;
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
