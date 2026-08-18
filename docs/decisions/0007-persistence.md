# ADR 0007 — Local persistence

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17
**Closes:** gap G09

## Context

`PLATFORM_CONTRACTS.md` § Persistence contract requires atomic persistence for profiles/policies,
content library, tag mappings, playback/resume and settings, and states that **unexpected power loss
must not corrupt the library**. That is the hard requirement: a device a three-year-old switches off
by pulling the plug must still have a working library afterwards.

Two constraints shape the answer and are easy to overlook:

- **The storage is an SD card on a Raspberry Pi.** It is the least reliable component in the system,
  and it wears out with writes. `CONFIGURATION_DEFAULTS.md` § 4 persists a resume position every
  10 seconds during playback, which is roughly 8,600 small writes per day. A naive
  rewrite-the-whole-file-each-time design would be both slow and destructive.
- **The device has no keyboard and may have a broken UI.** When something goes wrong, the maintainer
  needs to be able to inspect and fix state over SSH with a text editor.
  `CONFIGURATION_DEFAULTS.md` § 7 already commits to settings being hand-editable and therefore
  untrusted.

Language is Python per ADR 0001, which makes `sqlite3` available with no dependency at all.

## Decision

**Two stores, split by who needs to read them.**

### 1. Settings — TOML file, hand-editable

`settings.toml`, read at startup and on explicit reload. Contains only the **Manager** tier from
`CONFIGURATION_DEFAULTS.md` § 7: timeouts, brightness, volume ceilings, sleep timer, NFC debounce,
language.

- Written atomically: write to a temporary file in the same directory, `fsync` it, `os.replace()`,
  then `fsync` the directory. Anything less can leave a truncated file after power loss.
- **Every value is validated against the ranges in `CONFIGURATION_DEFAULTS.md` on read.** An
  out-of-range or unparseable value is clamped or replaced by the default, logged, and the file is
  left alone rather than silently rewritten. The file is untrusted input, not a cache of internal
  state.
- A malformed settings file must never prevent startup. Worst case AQENO runs on defaults and says so
  in the log.

### 2. Domain data — SQLite, one file

`aqeno.db`, via the standard library `sqlite3`. Holds the content library, content identities, source
resolutions, collections, tag mappings, profiles, policies and resume positions.

- **WAL mode** (`PRAGMA journal_mode=WAL`) — the reason this ADR is short. WAL survives power loss
  without corrupting the database, which is the actual requirement.
- **`PRAGMA synchronous=NORMAL`.** Under WAL this can lose the most recent commits on power loss but
  cannot corrupt the file. That is exactly the trade-off `CONFIGURATION_DEFAULTS.md` § 4 already
  accepted: resume error after power loss ≤ 12 s. `FULL` would fsync on every commit — 8,600 fsyncs a
  day to an SD card — to buy back a few seconds of audiobook position. Not worth it.
- **`PRAGMA foreign_keys=ON`.** Enforce the `DOMAIN_MODEL.md` invariants in the schema, in particular
  that deleting an NFC tag mapping cannot delete content.
- Resume positions live in their own narrow table, so the frequent small writes touch as few pages as
  possible.
- **A resume write is skipped when the position has not advanced** — paused playback writes nothing.
- One process-owned connection serves application, audio-callback and scheduled-checkpoint threads.
  The adapter permits cross-thread use but serialises every read, transaction and close operation;
  application code never coordinates SQLite access itself.

### 3. Media files are not in the database

The library stores a **stable AQENO content identity** (UUID, generated once) plus one or more source
resolutions. Moving or renaming a file breaks *resolution*, not *identity*: the item keeps its resume
position and tag mappings and reports itself unavailable. This is the `Content != Source` separation
from `DOMAIN_MODEL.md` made concrete, and it is why identity is not derived from the path.

### 4. Locations

| Path | Contents | Override |
|---|---|---|
| `$XDG_CONFIG_HOME/aqeno/settings.toml` | settings | `AQENO_CONFIG_DIR` |
| `$XDG_DATA_HOME/aqeno/aqeno.db` | domain data | `AQENO_DATA_DIR` |
| `$XDG_STATE_HOME/aqeno/logs/` | logs (gap G10) | `AQENO_STATE_DIR` |

Falling back to `~/.config`, `~/.local/share` and `~/.local/state`. The environment overrides exist so
tests never touch real state — `tests/` always points them at a temporary directory.

### 5. Schema versioning

- A `schema_version` table with a single integer row.
- **Forward-only migrations**, each a numbered Python module, applied in one transaction at startup.
- **The database file is copied before any migration runs.** On a device that may lose power at any
  moment, a mid-migration crash without a backup is how a library gets lost.
- A database whose version is *newer* than the code refuses to open. Downgrading silently is worse
  than failing.

### 6. Degraded operation

`AGENTS.md` requires that unsupported conditions fail clearly rather than partially pretending to
work. Therefore:

- A **read-only or full filesystem** is detected at startup. AQENO enters a degraded mode: local
  playback works, resume positions and settings changes do not persist, and this is logged and
  surfaced to a Manager — never to a child as an error.
- A **corrupt or unopenable database** does not crash. AQENO reports the failure, and recovery is an
  explicit Manager action, never an automatic wipe. Deleting a child's library to get the app to start
  is not an acceptable recovery strategy.

## Alternatives considered

**JSON or TOML files for everything, atomically replaced.** Maximally inspectable and debuggable, no
schema machinery, and genuinely attractive for a small personal project. Rejected for the library and
resume data: there are no transactions across multiple files, so a power cut between two related
writes leaves inconsistent state, and rewriting a whole library file every 10 seconds is the SD-card
wear problem in its purest form. Kept for settings, where inspectability matters more than
transactions and writes are rare.

**SQLite for settings too.** One store, one mechanism, less code. Rejected because a device without a
keyboard needs at least one piece of state that can be fixed with a text editor over SSH when the UI
will not start.

**An ORM (SQLAlchemy, Peewee).** Rejected as disproportionate. The schema is small, the queries are
simple, and `AGENTS.md` asks for boring technology and for dependencies that materially reduce
complexity. An ORM would add a dependency and an abstraction over an abstraction.

**A document store (TinyDB) or a key-value store (LMDB, `dbm`).** Rejected: TinyDB gives up the
durability guarantees that are the entire point here, and LMDB adds a dependency to do what `sqlite3`
already does from the standard library.

## Consequences

**Easier.** No dependency at all — `sqlite3` and `tomllib` are both standard library in Python 3.11+.
Power-loss durability is a property of WAL rather than something AQENO implements and gets subtly
wrong. SD-card wear is bounded by design. Settings remain fixable by hand.

**Harder.** Two stores means two code paths, two validation strategies and a rule about which data
belongs where. The rule is: *if a human might need to edit it without the UI, it is settings.*
Migrations must be written and tested even though the schema is small, because the first schema change
after real content exists is the one that matters.

**Constrained.** No domain object may hold a `sqlite3` handle: persistence sits behind a port like
every other adapter (ADR 0001's import boundary), so `application/` is testable with an in-memory
fake. Schema changes are forward-only, so a badly chosen column is corrected by a migration, never by
editing an existing one.

**Open verification.** Pull the power during playback, repeatedly, and confirm the library opens and
the resume position is within 12 s. This is a scenario test in ADR 0008, and it is the single test
that most directly protects the product requirement.
