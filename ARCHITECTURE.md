# AQENO Architecture

**Status:** pre-implementation architecture guardrails, not a final technology selection.

## Goals

AQENO must remain portable across supported Linux-capable hardware while sharing one product core across Kids, Easy and future experiences.

## Proposed logical boundaries

```text
UI / Presentation
      |
Application / Use Cases
      |
Domain
      |
Ports / Interfaces
      |
Adapters
  |       |       |       |
Audio   NFC    Hardware  Network/Cloud
```

## Domain concepts expected

- Content / ContentIdentity
- ContentSource
- PlaybackSession / ResumePosition
- User / Manager / Owner
- ExperienceProfile / Capabilities
- Action
- Scene / Context
- Device
- HardwareCapabilities

These names are provisional. Do not create abstractions before a use case requires them.

## Platform boundary

Hardware-specific implementations should sit behind explicit ports for at least:

- audio output/playback engine;
- display power/brightness state;
- physical controls;
- NFC reader;
- storage;
- network state;
- power/battery state where available;
- startup/readiness state and staged service initialisation.

The application must not depend directly on Raspberry Pi GPIO libraries or a particular SBC SDK.

## Startup architecture

AQENO uses staged readiness rather than waiting for the entire system to initialise before becoming usable.

Conceptually distinguish:

1. hardware/input availability;
2. local persisted state loaded;
3. local playback ready;
4. interactive UI ready;
5. network-dependent providers ready;
6. optional remote/cloud services ready.

Later stages must not unnecessarily block earlier local capabilities. Boot performance is measured on Reference hardware and protected against regressions.

## Display architecture

Display behaviour is an application-level state machine with at least `OFF`, `DIM`, `INTERACTIVE`, `AMBIENT` and `SETUP` states.

Do not equate playback state with display state. Do not rely solely on OS screensaver or desktop power-management semantics.

Ambient visual content has its own capability/permission boundary and source policy. For child profiles, enabling/configuring Ambient is Manager/Owner-controlled by default.

See `docs/product/DISPLAY_BEHAVIOR.md`.

## UI architecture

Kids, Easy and Standard should share components and domain state. Variation is driven by an experience/capability profile: text level, tile density, navigation depth, available actions, settings visibility and accessibility needs.

## Local-first boundary

The local device owns enough state to play local/downloaded content, resolve NFC assignments, preserve resume positions and apply local scenes without a cloud service.

Remote management, synchronisation and cloud backup are optional adapters added later.

## Decision still open

Do not lock these prematurely:

- SBC/reference production hardware;
- frontend framework;
- playback engine;
- local database;
- remote/cloud architecture;
- packaging/update mechanism;
- final open-source license.

Use feasibility spikes and ADRs before committing.
