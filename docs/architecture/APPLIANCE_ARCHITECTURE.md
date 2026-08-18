# AQENO Appliance Architecture

**Status:** Canonical target architecture; implementation is staged below.
**Date:** 2026-08-18
**Decisions:** ADR 0020 and ADR 0021

AQENO is the product. Linux, a platform image and a particular storage device are replaceable
implementation details. This document is the canonical overview; detailed storage/recovery and
platform/install rules live in the contracts linked below.

## 1. Audited pre-slice state

### What already fits

- Domain and application code do not import Raspberry Pi GPIO/I2C libraries. Audio, display,
  controls, LEDs and NFC sit behind ports (`ARCHITECTURE.md`, ADR 0010).
- Stable content UUIDs are distinct from source locations. Fingerprints permit a moved file to be
  re-associated without losing progress, token mappings or metadata (ADR 0007, ADR 0014).
- SQLite is embedded, transactional, indexed for the current library scale and configured with WAL,
  `synchronous=NORMAL` and foreign keys. A server database is neither required nor justified.
- Settings writes and media/artwork uploads use same-filesystem temporary files, `fsync` and atomic
  replacement. Ingestion runs off the playback thread and a scan never deletes missing media.
- The Device UI, local Management API and static Admin client run from one AQENO composition root;
  Management failure does not own or block playback. No browser runtime is needed on the appliance.
- The systemd prototype runs AQENO unprivileged and applies useful service sandboxing.

### Persistent locations before the NOW implementation

| State | Current resolver | Current reference-service value | Target class |
|---|---|---|---|
| `settings.toml` | `AQENO_CONFIG_DIR` / XDG config | `/etc/aqeno` | A |
| `aqeno.db`, extracted/custom artwork | `AQENO_DATA_DIR` | `/var/lib/aqeno` | A (artwork split A/C) |
| management key and device ID | `AQENO_STATE_DIR` | `/var/lib/aqeno/state` | secret/device-local |
| imported media | `AQENO_MEDIA_DIR` | `/var/lib/aqeno/media` | B |
| logs | standard logging to stderr | journald under system policy | diagnostic, not A |
| Admin/Device UI assets | installed Python/package files | `/opt/aqeno` | reconstructable release |

The XDG defaults remain appropriate for developer workstations. A production appliance must set all
four directory overrides to the mounted Data Contract and must never silently fall back to a home or
root filesystem when that mount is absent.

### Contract conflicts and risks

| Existing state | New invariant | Resolution |
|---|---|---|
| `AQENO_CONFIG_DIR=/etc/aqeno` contains user settings | Reinstalling SYSTEM preserves AQENO | Move user settings below `AQENO-DATA`; keep only reconstructable bootstrap/environment data in `/etc/aqeno`. |
| Service writes to `/var/lib/aqeno` and `/var/cache/aqeno` | Valuable state has a separately detectable mount | Bind every persistent root below `/aqeno-data`; refuse to create a replacement database on SYSTEM if the mount is missing. |
| Service waits for `network-online.target` | Local playback and NAS-independent boot | Remove network-online ordering; network and external sources become asynchronous degradation. |
| Installer assumes a mutable checkout at `/opt/aqeno` | Reproducible, rollbackable releases | Install a wheel plus bundled UI into a versioned release and switch `current` atomically. |
| Migration backup copies DB, WAL and SHM as ordinary files | Backups of a live WAL database are consistent | Replace it before real user migration with SQLite's online backup API and validation. The transaction remains useful but is not itself a backup. |
| Artwork is one directory and may be deleted through Management | Manual artwork is irreplaceable; extracted thumbnails are reconstructable | Separate original/custom artwork (A) from derived cache (C), with an explicit migration. |
| Device ID and management key share generic state | Portable restore must not clone appliance identity/secrets accidentally | Store them in a device-local secrets/identity area and exclude them from portable state backup by default. |
| No capacity or mount guard exists | ENOSPC and missing Data must not corrupt/fork state | Add mount identity, free-space thresholds and write admission before imports/backups/migrations. |

Those audited deployment files were a development prototype. The current reference installer now
implements the bounded NOW slice (Data validation/migration, versioned release and systemd/Avahi
integration), but it remains neither a partitioner nor a repair tool and must not be used as one.

## 2. Target layers

```text
AQENO Device UI ───── Local Management API + Admin assets
                 \   /
             AQENO Application / Domain
        playback, library, profiles, policies, ingestion
                         |
       ports + capability-oriented platform composition
                         |
      Reference Platform 1 adapter and system integration
       Qt/DRM, GStreamer, input, I2C/SPI/GPIO, networking
                         |
          Raspberry Pi OS Lite 64-bit / systemd
                         |
               Raspberry Pi 4B hardware

Persistent boundary: /aqeno-data (not part of a release or SYSTEM)
```

Only Reference Platform 1 is supported now. A future board is supported only after its adapter,
package baseline and hardware validation pass; a capability-shaped boundary is not a support claim.

## 3. Runtime and boot

Reference Platform 1 uses Raspberry Pi OS Lite 64-bit, without a desktop environment. The minimal
roles are systemd, basic networking/mDNS, Python, Qt 6/QML with the selected direct display stack,
GStreamer, touch/input, I2C/SPI/GPIO access and AQENO's declared Python dependencies. Exact packages
belong to the pinned platform manifest, not the Core.

The current single AQENO process remains the preferred topology: it avoids IPC and preserves early
physical playback readiness. The FastAPI adapter and static Admin assets are optional surfaces inside
that process. A separate service is introduced only when measured fault or privilege isolation needs
it. AQENO itself runs as `aqeno`, never root.

Boot ordering is:

```text
kernel/systemd -> validate and mount AQENO-DATA -> AQENO process
              -> LOCAL_READY -> PLAYBACK_READY -> UI_READY
              -> network/external sources when available
```

Display-capable platforms may cover unavoidable OS startup with a branded platform presentation.
It is neither a Core state nor a readiness dependency. RH1 uses Plymouth only after its real display
path is validated; the first Device UI frame dismisses it with no minimum duration. Headless AQENO
does not install or wait for boot graphics.

Missing or invalid AQENO-DATA is a named data failure. AQENO must not initialize an empty database on
SYSTEM. NAS mounts are not boot dependencies. A broken UI or Management surface leaves playback and
physical controls alive, as already required by `READINESS_STATES.md`.

## 4. Failure and recovery model

| Failure | Required behavior |
|---|---|
| OS will not boot | Reimage/repair SYSTEM; leave AQENO-DATA untouched. |
| AQENO release fails | Keep data; select the previous compatible application release or repair it. |
| AQENO-DATA absent/unreadable | Stop stateful startup, report data failure through bounded recovery/diagnostics; never format or create shadow state. |
| SQLite corrupt | Preserve evidence, validate known backups, require explicit restore/repair; never wipe. |
| Filesystem read-only/full | Continue safe reads/playback, reject writes/imports early, expose Manager diagnosis. |
| Power loss during import | Existing library remains valid; incomplete staging is disposable and cleaned at startup. |
| Power loss during backup | `.partial` output is never listed as valid; last validated backup remains intact. |
| Failed schema migration | Original validated snapshot remains; do not activate the new release. |
| NAS unavailable | Boot and local playback continue; indexed items remain known but unavailable. |
| Hardware missing | Advertise degradation by capability; do not impersonate support with a fake adapter. |
| Whole card lost | Install on new media and restore a separately stored AQENO backup. |

## 5. Decisions by horizon

### NOW — implemented in the repository; RH1 validation remains

1. Adopt the Storage and Platform/Install contracts and amend ADR 0007's appliance locations.
2. Introduce one resolved appliance path layout plus a Data-volume marker/mount guard.
3. Move production settings, database, media and durable artwork to `/aqeno-data`; migrate existing
   prototype paths without deleting originals.
4. Replace raw WAL migration copies with a validated SQLite snapshot mechanism.
5. Implement the state-backup engine and manifest before exposing restore.
6. Replace the prototype checkout installer/service with a versioned, idempotent Pi 4 installation
   slice and test it on a clean card.
7. Add capacity, interrupted-import cleanup and data-failure checks.

### NEXT — after the storage slice is proven on Reference Hardware

- restore with preflight/staging/rollback; explicit Repair and reset commands;
- Management API for validated backup creation/download and restore planning;
- full-media backup destination adapters for USB/NAS and an independent scheduler;
- reproducible Pi image using the same provisioning primitives;
- privileged helper only for the fixed operations that actually require it;
- diagnostic export and reference-hardware power-loss tests.

### LATER

- recovery partition/environment: useful only once its independent update/security burden is
  justified; external reimage plus portable backup is the current recovery path;
- A/B OS slots: useful for unattended OS/firmware updates, but unjustified now. Versioned application
  rollback covers the immediate risk. A future image/storage-layout version may introduce slots;
- additional platform images, OTA/fleet infrastructure and encrypted portable secret bundles.

Neither a recovery partition nor A/B slots are rejected. Reserving and maintaining them now would add
more failure modes than they remove from this prototype.

## 6. Scenario quality gate

The ten scenarios in the architecture brief resolve as follows: SYSTEM repair preserves Data; whole
card loss restores from an external backup; replacement Pi 4 uses the same supported platform; a
future supported board consumes the portable state; NAS never gates boot; import and backup staging
are atomic; updates never own user data; corrupt Data is never formatted; and state-only backup does
not copy NAS audio. These are contract tests for the implementation, not assumptions.

## 7. Canonical document map

- appliance overview, audit, failure model and priorities: this document;
- filesystem, data classes, backup/restore/reset: `STORAGE_BACKUP_RECOVERY_CONTRACT.md`;
- platform capabilities, install, boot, packaging and updates: `PLATFORM_INSTALL_CONTRACT.md`;
- hardware ports and runtime semantics: `PLATFORM_CONTRACTS.md`;
- persistence technology: ADR 0007, amended by ADR 0020;
- durable decisions: ADR 0020 and ADR 0021;
- Reference Hardware bill of materials: `docs/hardware/HARDWARE_REFERENCE.md`.

Other deployment documents must reference these contracts rather than restating them.
