# Storage, Backup and Recovery Contract

**Status:** Canonical target contract; implementation status is recorded in § 9.
**Authority:** ADR 0020

## 1. Reference storage layout

Reference Platform 1 uses three partitions on a normal 256-GB microSD:

| Partition | Filesystem | Purpose | Reference size |
|---|---|---|---|
| firmware boot | FAT as provided by Raspberry Pi OS | bootloader, firmware, kernel handoff | base-image default |
| SYSTEM | ext4 | OS, packages, AQENO releases, bounded logs/cache | 16 GiB |
| `AQENO-DATA` | ext4, label `AQENO-DATA` | all valuable AQENO state and local media | remainder |

Sixteen GiB is a reference value, not an application assumption. Provisioning must check the pinned
base image and retain at least 25% free SYSTEM space after installation. Cards too small to satisfy
that and the requested media reserve are rejected. The installer does not partition automatically;
explicit image/provisioning is a separate destructive operation.

`AQENO-DATA` mounts at `/aqeno-data` by filesystem UUID (label is diagnostic). Use normal ext4
journaling and conservative durability defaults; `errors=remount-ro` is preferred. No long journal
commit interval, disabled barriers or other wear optimization may weaken integrity. Filesystem checks
run through the platform's normal boot policy. Swap and persistent journald usage are bounded by the
platform manifest.

The volume contains an AQENO marker with `data_format_version`, a generated volume ID and creation
time. A valid marker and expected mount identity are prerequisites for stateful startup. A plain
directory accidentally created on SYSTEM is not a Data volume.

## 2. Directory and ownership contract

```text
/aqeno-data/
  volume.json                 # Data-volume marker; A
  state/
    aqeno.db                  # A
    config/settings.toml      # A
    artwork/original/         # A: uploaded/manually selected originals
    identity/                 # device-local, not portable by default
    secrets/                  # device-local secrets, mode 0700
  media/                      # B: AQENO-managed local audio
  cache/
    artwork/                  # C: embedded extracts/thumbnails
    index/                    # C: rebuildable indexes if introduced
  tmp/
    imports/                  # D; same filesystem as media for atomic publish
    backup/                   # D; incomplete archives end in .partial
    restore/                  # D; validated restore staging
  backups/                    # completed local backup artifacts; not the sole backup
```

The volume root is owned by root and not generally writable. AQENO-owned directories are
`aqeno:aqeno`, mode `0750`; `state/secrets` and secret files are `0700`/`0600`. The Management API
runs as `aqeno`. Platform/bootstrap files under `/etc/aqeno` are root-owned and reconstructable.

## 3. Data classes

| Class | Includes | Repair | State backup | Full backup |
|---|---|---|---|---|
| A — irreplaceable | DB, profiles, favorites, progress, token/access rules, corrected metadata, settings including logical control mappings, original custom artwork | preserve | include | include |
| B — user media | locally imported/managed audio | preserve | exclude, inventory only | include on request |
| C — reconstructable | extracted artwork, thumbnails, generated search/index caches | may clear | exclude | exclude |
| D — ephemeral | partial uploads, processing and backup/restore staging | may clear safely | exclude | exclude |

NAS audio is never B on AQENO-DATA. Its stable content identity, metadata, availability and logical
source description are A; credentials are secrets. A missing source never deletes these records.

Device identity, the local Management key, the Admin password verifier and live sessions are
deliberately not part of a portable state backup. Repair preserves them because Data remains in
place; a restored replacement requires new physical ownership setup. Portable NAS or
Wi-Fi secrets are also excluded until an explicit encrypted-secret export exists; restore reports
which connections require credentials again.

## 4. Capacity and write admission

Capacity is evaluated on the target filesystem, not by summing library metadata. Defaults for the
reference volume are:

- warning below 10% free or 5 GiB, whichever threshold is reached first;
- critical below 3% free or 1 GiB;
- every import, full backup and migration additionally requires its measured/estimated payload plus
  10% staging margin.

At warning level AQENO remains functional and surfaces Manager guidance. At critical level it rejects
new imports, backup staging and nonessential cache generation before ENOSPC; existing playback and
essential narrow state writes remain attempted. Cache eviction may reclaim only Class C/D. It may
never delete A/B. Thresholds are platform defaults, not profile settings.

## 5. SQLite durability and migration

SQLite remains the database. WAL, foreign keys and serialized access remain accepted. The current
`synchronous=NORMAL` trade-off is retained for frequent resume writes; it can lose the newest commit
on sudden power loss but must not be used as an excuse for unsafe filesystem settings.

Before a schema migration that touches existing data:

1. verify Data mount, database integrity, supported schema and free space;
2. create a consistent snapshot using SQLite's online backup API into staging;
3. run `PRAGMA integrity_check` on the snapshot;
4. record source/target schema and checksum;
5. apply all pending migrations in one transaction;
6. validate the migrated database before activating the new release.

Copying the database, WAL and SHM sequentially is not the backup contract. Existing `.bak-*` files
are legacy safeguards until replaced and are not advertised as validated backups.

## 6. Portable `.aqbackup` format

An `.aqbackup` is a ZIP64 archive with a UTF-8 `manifest.json` at its root. ZIP64 is chosen because it
is inspectable and available in the Python standard library; implementations stream entries and do
not buffer a full media archive in memory. Format version 1 contains:

```json
{
  "backup_format_version": 1,
  "aqeno_version": "0.1.0",
  "created_at": "2026-08-18T12:00:00Z",
  "schema_version": 4,
  "kind": "state",
  "included_components": ["database", "settings", "original_artwork"],
  "media_included": false,
  "entries": [{"path": "state/aqeno.db", "size": 1234, "sha256": "..."}]
}
```

Unknown format versions are rejected. Device ID, board model, Linux files, firmware, boot settings
and hardware device paths are not restore prerequisites. Every payload entry has size and SHA-256;
paths are normalized and may not escape the restore root.

Creation is: consistent DB snapshot → collect immutable inputs → stream to destination `.partial` →
fsync when locally meaningful → reopen and verify manifest, sizes, checksums and DB integrity →
atomic rename to `.aqbackup`. Only the final name is listed as valid. A destination is an adapter
(download stream, USB, mounted NAS); scheduling is a separate application concern.

State backup includes Class A and a media inventory/source description. Full backup adds Class B and
may be very large. Neither type includes C, D or Linux. A backup stored only on the same microSD is a
convenient restore point, not protection against card loss.

## 7. Restore

Restore is a planned, exclusive mutation, not an upload overwrite:

1. stream into `tmp/restore` with a size limit and no archive extraction yet;
2. validate format, paths, checksums, schema compatibility and required space;
3. show a restore plan including excluded secrets, unavailable external sources and migrations;
4. make a validated snapshot of current Class A state;
5. stop ingestion and state mutations while playback is stopped or explicitly quiesced;
6. extract to staging, migrate there if required, validate, then atomically switch state roots;
7. retain the previous state until the restored installation passes health checks.

Same-device, new-card and replacement-Pi restores use this flow. A future supported platform may
restore the same portable state; its adapter maps hardware-independent preferences to its devices.
Platform-specific configuration is detected again. NAS items remain indexed and unavailable until
their source is reconfigured/reconnected; they are never deleted merely because restore is offline.

Logical control mappings are portable AQENO preferences. Restore preserves mappings for logical
controls even when the target hardware does not expose them; unavailable entries remain dormant.
Unknown actions are not executed or silently remapped. A compatible replacement control can reuse
the semantic mapping without carrying I2C addresses, GPIO numbers or board identities in the backup.

## 8. Repair and reset

| Operation | May change/delete | Must preserve |
|---|---|---|
| Repair | SYSTEM packages, AQENO releases, platform/bootstrap config, C/D | all A/B on AQENO-DATA |
| Reset device preferences | `settings.toml` values to documented defaults; device bootstrap secret may be rotated only if explicitly selected | DB/library, profiles, access, tokens, favorites, progress, media, artwork |
| Complete factory reset | all AQENO-DATA, including Admin credential/sessions/bootstrap ownership, after explicit authenticated intent, exact impact display and separate destructive confirmation | nothing on Data; external NAS media is never deleted |

Repair never formats Data. Unknown, incompatible or damaged Data stops repair for an explicit
decision. Complete reset is not an error-recovery fallback; implementations should prefer moving old
state to a recoverable quarantine when space permits before permanent deletion.

## 9. Implementation status and API boundary

Implemented today: SQLite WAL persistence; the versioned Data-volume marker and fail-closed mount,
permission, layout and capacity guard; the classified directory layout; resumable non-destructive
prototype migration; consistent SQLite online snapshots; atomic validated state `.aqbackup` creation;
read-only backup validation; import capacity admission and atomic staging cleanup. Stable media
identity, unavailable external-media semantics and background ingestion remain intact. Not
implemented: restore execution, Full Media Backup, factory reset execution, scheduled/destination
adapters or an Admin API for these operations.

The current Management API has no backup/restore contract. The local engine is deliberately not
exposed through ad-hoc routes. Future endpoints may create/list/validate/download backups and
produce/execute restore plans, but are an API gap, not implied functionality.
Restore, reset, mount and reboot must never accept arbitrary shell commands or paths.
