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
- accept semantic navigation inputs — move focus, activate, Home — so the everyday journey is
  operable without touching the panel and without looking (ADR 0024, ADR 0026);
- support simulated NFC before physical NFC is required;
- implement display states `OFF`, `INTERACTIVE`, `SETUP`; `DIM` and `AMBIENT` may be stubbed;
- continue audio with display fully off;
- implement a Night/Dark-Room policy;
- provide only the bounded on-device setup/recovery controls required by the slice, without complex
  free-text entry;
- provide structured local logs without telemetry.
- provide authenticated local management for import, library metadata/artwork, token assignment and
  relevant device configuration without cloud dependency; its Web client remains replaceable.

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
The MVP is complete when the first vertical slice works on desktop Linux and Reference Hardware,
automated core tests pass, and the dark-room, offline and touch-free scenarios can be demonstrated
without special developer intervention. The touch-free scenario is automated today and is a physical
RH1 acceptance item once a SELECT encoder exists on the box; PREVIOUS, NEXT, HOME and VOLUME
already do.
