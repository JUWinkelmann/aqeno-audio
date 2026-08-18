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

- verify the left/right MX defaults (Previous/Next), change one allowed mapping, reboot, then restore
  defaults;
- encoder rotation changes volume, short press toggles Play/Pause, and long press never also emits
  short press;
- bounce, rapid input and simultaneous presses are harmless;
- encoder/NeoKey feedback is restrained, semantic and completely off in Bedtime;
- controls retain meaning while the display is OFF and do not wake it routinely.

## Display and touch

- actual output is 800×480 at 60 Hz, touch targets remain reliable at edges;
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
