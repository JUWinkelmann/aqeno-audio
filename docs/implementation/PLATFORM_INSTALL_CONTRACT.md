# Platform, Installation and Update Contract

**Status:** Canonical target contract; Reference Platform 1 implementation is incomplete.
**Authority:** ADR 0021

## 1. Platform boundary

AQENO selects implementations by required capability, not by board-name branches in Domain or
Application. Existing ports remain the runtime boundary:

| Capability | Boundary / responsibility |
|---|---|
| audio output | `AudioEngine`; platform chooses GStreamer devices/pipeline integration |
| display/touch | `DisplayPanel` plus Qt input; platform configures DRM/Wayland/eglfs and panel |
| semantic controls | `InputBus`; platform maps GPIO/I2C/SPI devices to AQENO events |
| LEDs | `StatusLeds`; product policy remains in Application |
| NFC | token input port; reader/bus details remain in adapter |
| storage | Data mount validation and capacity facts; content identity remains in Core |
| network | availability/source adapters; never a local-readiness prerequisite |
| power/system | narrowly enumerated platform operations when implemented |

No generic HAL, board inheritance tree or dynamic layout language is introduced. The composition root
receives a validated platform descriptor/capability set and wires only real adapters. Missing required
capability is explicit degradation or incompatibility, never a fake production adapter.

## 2. Reference Platform 1

The sole supported appliance platform is Raspberry Pi 4B with the hardware in
`docs/hardware/HARDWARE_REFERENCE.md`, running a pinned Raspberry Pi OS Lite 64-bit release. Desktop
Linux remains a development target, not a second appliance platform. Pi Zero 2 W, Pi 5, other ARM64
boards and x86_64 are unsupported until separately validated.

Platform-owned configuration includes boot firmware settings, device-tree overlays, enabled buses,
audio/display selection, udev/group permissions, Data mount, systemd units, Avahi and the pinned OS
package manifest. AQENO-owned preferences such as volume ceilings, display behavior and profiles are
portable state and do not contain ALSA card numbers, GPIO paths or Pi device identifiers.

The minimum system roles are:

- systemd and mount/fsck support;
- basic LAN networking and mDNS; neither gates local startup;
- Python runtime and per-release virtual environment;
- Qt 6/PySide6/QML and the selected direct display stack, with no desktop environment;
- GStreamer/PyGObject and required codecs;
- evdev/touch plus I2C/SPI/GPIO access needed by acquired hardware;
- AQENO wheel with bundled Device/Admin assets.

The exact packages and versions are a reproducible platform manifest established during the RH1
spike. Packages are not installed merely because a desktop image normally includes them.

## 3. Packaging and release layout

Use a wheel and versioned application releases, not a container and not a mutable Git checkout:

```text
/opt/aqeno/
  releases/<release-id>/
    venv/
    release.json
  current -> releases/<release-id>
```

Qt/PyGObject may remain pinned system packages where Debian integration makes pip packaging
unreliable; that choice is part of the platform manifest. Python dependencies and static UI assets
are installed into the release. A staged release is immutable after validation. Switching `current`
is atomic, and only schema-compatible releases may be selected for rollback.

Containers add image, device-access and lifecycle complexity without isolating a current risk, so
they are rejected for Reference Platform 1.

## 4. Installer contract

The AQENO installer applies a generic release through a selected supported platform implementation.
It is idempotent and phase-based:

1. detect OS/architecture/platform and validate Reference Platform requirements;
2. inventory Data devices and existing AQENO-DATA without mounting arbitrary input paths;
3. validate marker, filesystem, ownership, schema compatibility and free space;
4. install system dependencies from the pinned manifest;
5. build/install a release in a new staging directory;
6. install reconstructable platform integration and service sandbox;
7. run offline checks against staging and Data without changing the active release;
8. atomically activate, start and verify local readiness;
9. retain logs and the previous compatible release.

Re-running a completed phase is harmless. Every failure names the phase, leaves the prior release and
Data intact, and provides a log. `--dry-run` performs detection, inventory and a change plan without
writes. The installer never partitions/formats by default and never treats unknown Data as empty.

The current `deploy/install-reference-service.sh` is still a reference bootstrap helper rather than
the complete installer contract. It now fails closed without a marked AQENO-DATA mount, installs a
versioned release atomically, builds the Admin client and installs bounded systemd/Avahi integration.
It also invokes the resumable non-destructive prototype-data migration before activation. Platform
compatibility discovery, dry-run and full installer phase journaling remain unimplemented.

## 5. Service and privilege contract

Prefer one `aqeno.service`, ordered after local filesystems and the validated AQENO-DATA mount, not
after `network-online.target`. It runs as `aqeno`, has only the hardware groups/device permissions
required by the selected adapter, and writes only to the Data/cache directories named by the Storage
Contract. The release and SYSTEM are read-only to it. Failure restarts are bounded to avoid loops that
wear storage or hide a persistent data error.

The Management API is not root. If reboot, update, mount or repair later need privilege, a separate
small helper exposes fixed named operations with validated value parameters over a local authenticated
IPC boundary. It never executes client-provided commands, shell fragments or arbitrary mount paths.

## 6. First boot and existing Data

First boot is a persistent, resumable sequence: validate platform → locate or explicitly initialize
AQENO-DATA → create its marker/layout atomically → generate device-local identity/secrets → initialize
or validate schema → activate services → expose setup state. Each completed phase is recorded only
after validation. A power cut repeats the incomplete phase safely.

If AQENO-DATA already exists, first boot validates and adopts it; it never overwrites it. A newer,
unknown, damaged or ambiguous format stops with a recovery diagnosis. Initialization is allowed only
for storage explicitly selected as empty during provisioning.

## 7. Installer, image and recovery

An installer adds AQENO to a supported base. An image packages a pinned base OS, the same release and
the same provisioning primitives for one platform. An image is a convenience distribution, not
AQENO's identity. Image generation must be automated from pinned inputs; a hand-maintained golden SD
card is forbidden.

A dedicated recovery partition is **LATER**. Today, repair means reimaging/reinstalling SYSTEM while
preserving or restoring Data. A/B SYSTEM slots are also **LATER**; application-release rollback solves
the current failure class more cheaply. Introducing either later requires a new versioned storage
layout and migration path, not assumptions embedded in Core.

## 8. Update ownership

| Update class | Owner | Atomicity / failure rule |
|---|---|---|
| AQENO application | release installer | stage, validate, atomic `current` switch |
| DB schema | persistence migration runner | validated pre-snapshot, transaction, post-check |
| Admin and Device UI | AQENO application release | versioned with compatible API/application |
| platform packages | Reference Platform adapter/manifest | explicit compatibility check and reboot plan |
| OS | platform maintenance/image path | must preserve AQENO-DATA; not an app script side effect |
| firmware/boot config | platform adapter | explicit, platform-specific, recoverable procedure |

There is no universal `update.sh`. An application rollback cannot open a newer incompatible schema;
release metadata declares its supported schema range. Risky migrations require enough space for the
snapshot and restored old state before activation.

## 9. Platform migration

On a future supported board: install its platform image/adapter, restore the portable AQENO backup,
generate new device identity/management key, rediscover hardware, re-enter excluded credentials and
map product-level preferences to local adapters. Library identity, profiles, access, favorites,
progress, token assignments, settings, metadata and custom artwork are portable. Boot files, device
nodes, bus numbers, card indices, drivers and caches are not.

## 10. First implementation slice

The first slice stops before partitioning or image creation:

1. implement a typed resolved path layout and Data-volume validator;
2. make the systemd environment point every durable path below `/aqeno-data` and remove network boot
   ordering;
3. refuse appliance startup when the required mount/marker is absent, while keeping XDG developer
   behavior unchanged;
4. implement a non-destructive migration command that copies current prototype state to staging,
   validates it, then publishes it without deleting the source;
5. replace migration file copies with a tested SQLite online snapshot primitive;
6. implement and contract-test state backup creation/validation only;
7. validate on a clean Pi 4 card and under forced power interruption before restore or partitioning.

This slice creates the safety foundation needed by a later installer. It does not add alternate-board
adapters, a recovery UI, A/B updates, automatic backup or a new Management API surface.
