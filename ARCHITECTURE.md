# AQENO Architecture

**Status:** implemented First Vertical Slice architecture; physical RH1 validation remains.

## Goals

AQENO must remain portable across supported Linux-capable hardware while sharing one product core across Kids, Easy and future experiences.

## Proposed logical boundaries

```text
Device UI          Future Management UI
Qt Quick/QML       responsive client
      |                    |
Python view models   Management API adapter
      +---------+----------+
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

The appliance, storage and installation boundary is defined by ADR 0020, ADR 0021 and
`docs/architecture/APPLIANCE_ARCHITECTURE.md`. Raspberry Pi 4B is Reference Platform 1, not the AQENO
architecture. Production state lives on the separately validated `AQENO-DATA` volume; Linux and
versioned application releases are replaceable.

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

The Qt Quick/QML Device UI is an appliance presentation, not an administration application. QML
renders application state and emits intentions through concrete Python view models; product rules
stay in Core/Application. Complex administration uses the separately authenticated, local-first
FastAPI adapter defined by ADR 0018 and `docs/management/LOCAL_MANAGEMENT_API.md`. Its client is
replaceable and optional; playback never depends on HTTP, LAN or a Management UI (ADR 0012).

## Local-first boundary

The local device owns enough state to play local/downloaded content, resolve NFC assignments, preserve resume positions and apply local scenes without a cloud service.

Local ownership and administration are exposed by the on-device Management API without a cloud
service. Remote management, synchronisation and cloud backup are optional adapters added later.

## Decisions made

See `docs/decisions/`. Accepted ADRs override this document.

- language and runtime — Python 3.11+ (ADR 0001);
- UI stack — Qt 6 via PySide6 with QML, in-process with the core (ADR 0002);
- playback engine — GStreamer via PyGObject (ADR 0003);
- internationalisation — German and English (ADR 0005);
- local persistence — SQLite in WAL mode plus a hand-editable TOML settings file (ADR 0007);
- test strategy (ADR 0008);
- content kinds and their playback behaviour (ADR 0009).
- Core/hardware/optional-service separation (ADR 0010);
- synchronous semantic input delivery (ADR 0011);
- Device UI and future Management UI boundary (ADR 0012);
- physical token/content separation (ADR 0013);
- local content ingestion and identity (ADR 0014);
- excellence-first personal-project posture (ADR 0015);
- application authority over display power policy (ADR 0016);
- display as an optional capability without a capability framework (ADR 0017).
- replaceable SYSTEM, classified Data and portable backup (ADR 0020);
- capability-oriented platform, Reference Platform 1 and installer/image boundary (ADR 0021).

## Decision still open

Do not lock these prematurely:

- production hardware beyond the acquired RH1 prototype;
- final Reference Platform package manifest and display server — `eglfs` vs Wayland gates the
  display-power story (gap G24); packaging/install boundaries are decided by ADR 0021;
- remote/cloud architecture;
- final open-source license — **deferred by intent**, see ADR 0006. AQENO is a personal project;
  nothing is published or distributed, so no licence is needed yet.

Use feasibility spikes and ADRs before committing.
