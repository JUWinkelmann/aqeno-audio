# ADR 0020 — Replaceable system and portable AQENO data

**Status:** Accepted
**Date:** 2026-08-18
**Amends:** ADR 0007 location and migration-backup details

## Context

ADR 0007 selected appropriate persistence technologies but described desktop/XDG locations, not an
appliance failure boundary. The service prototype subsequently placed settings in `/etc/aqeno` and
the database/media in `/var/lib/aqeno`, all on the replaceable OS filesystem. Reinstalling Linux would
therefore risk losing AQENO or silently starting an empty library.

The appliance must survive SYSTEM repair, support whole-card restore and keep future platform
migration possible. A separate partition improves fault isolation but is not itself a backup.

## Decision

All irreplaceable AQENO state and AQENO-managed local media live on a separately identifiable
`AQENO-DATA` volume mounted at `/aqeno-data`. Production startup validates the volume marker and mount
identity and must not fall back to a directory on SYSTEM. Platform/bootstrap configuration remains
reconstructable on SYSTEM; product/user configuration belongs to Data.

Data is classified as irreplaceable state, user media, reconstructable data or ephemeral data. Repair
preserves the first two classes. Factory reset is a distinct, explicit destructive operation.

Portable backups contain AQENO state, not Linux or platform configuration. State and full-media
backups use a versioned `.aqbackup` manifest with checksums and are offered only after validation.
SQLite snapshots use the online backup API; a sequential raw copy of a live DB/WAL/SHM set is not a
backup contract. Device identity, the local Management key and platform-specific secrets are excluded
from portable state backup by default.

The detailed normative contract is
`docs/implementation/STORAGE_BACKUP_RECOVERY_CONTRACT.md`.

## Consequences

- SYSTEM can be repaired or replaced without owning user data.
- A missing Data mount fails closed instead of creating a divergent empty library.
- Existing `/etc/aqeno` and `/var/lib/aqeno` prototype state needs a non-destructive migration.
- Backup/restore gains a format and integrity contract; it is more work than copying a partition but
  is portable across future supported hardware.
- ADR 0007's SQLite/TOML choices, WAL and `synchronous=NORMAL` remain accepted. Its XDG locations are
  development defaults; appliance locations are now governed here.
- ADR 0007's current `.bak-*` implementation is a legacy safeguard to replace before migrations of
  real user data; it is not a validated backup.

## Alternatives considered

Keeping all state on the root filesystem makes installation simpler but makes Linux reinstall own
AQENO data and was rejected. A raw partition image includes OS/platform assumptions, wastes space and
does not provide portable selective restore. PostgreSQL adds a server lifecycle without solving the
storage failure boundary and was rejected.
