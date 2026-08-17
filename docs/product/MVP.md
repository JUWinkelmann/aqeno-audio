# AQENO MVP

## Goal
Prove the AQENO product architecture with one coherent vertical slice before expanding features.

## MVP must
- boot into a usable local-first player without network dependency;
- expose a Kids Early UI with a small library of local content;
- play local audio reliably;
- support HTTP audio stream and one podcast/RSS path behind the same content abstraction;
- persist playback/resume state;
- accept semantic Play/Pause, Next, Previous and Volume inputs;
- support simulated NFC before physical NFC is required;
- implement display states `OFF`, `INTERACTIVE`, `SETUP`; `DIM` and `AMBIENT` may be stubbed;
- continue audio with display fully off;
- implement a Night/Dark-Room policy;
- provide a minimal local Manager configuration surface;
- provide structured local logs without telemetry.

## Explicitly not MVP
- cloud accounts or remote management;
- commercial streaming services;
- recommendations/AI;
- multi-device follow-me;
- full multi-user;
- production enclosure/electronics;
- mandatory battery;
- photo-frame/Ambient as a finished feature;
- app-store style plugins.

## Exit criteria
The MVP is complete when the first vertical slice works on desktop Linux and Reference Hardware, automated core tests pass, and the dark-room and offline scenarios can be demonstrated without special developer intervention.
