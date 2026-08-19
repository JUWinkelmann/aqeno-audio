# ADR 0014 — Content ingestion: discovery, identity and metadata

**Status:** Accepted; § 2 and § 5 superseded by ADR 0028 (2026-08-19)
**Date:** 2026-08-18
**Accepted:** 2026-08-18
**Closes:** gap G14 (with `docs/implementation/CONTENT_INGESTION.md`)

> **Superseded in part.** ADR 0028 keeps everything this ADR decided about *how* content is discovered
> and identified — the `mutagen` port, the fingerprint, work grouping, the long-form default, the
> `aqeno.toml` sidecar, and "nothing is ever deleted by a scan". It replaces two things: **§ 2's
> startup scan** (preparation is now only ever explicitly triggered) and **§ 5's incremental commit**
> (results now land in a candidate revision that is published atomically). Read § 2 and § 5 below as
> history; ADR 0028 § 1 and § 3 are current.

## Context

`FIRST_VERTICAL_SLICE.md` items 2–4 require three local items on the Kids Early surface, playable and
resumable. Nothing in the code produces them: `Library.list_content()` is empty and no scan exists.
This is gap G14, and `AGENTS.md` forbids inventing the missing decisions in an implementation.

Three constraints make this more than "walk a folder and read tags":

- **ADR 0007 § 3 forbids deriving identity from a path.** A `ContentId` is a UUID generated once, and
  moving a file must break resolution, not identity. So a rescan needs a way to recognise a file it
  has already seen at a different path — otherwise every reorganisation of the media folder silently
  duplicates the library and orphans resume positions and tag mappings.
- **ADR 0009 § 4 makes a folder of forty MP3s one item with forty chapters**, with chapter sources
  ranked embedded → CUESHEET/`.cue` → playlist → track number → natural filename order, and tags read
  in three dialects (ID3, Vorbis, MP4 atoms). That is a real metadata problem, not a `Path.glob()`.
- **ADR 0009 § 5 makes the content kind a guess.** Kind drives `Next`, `Previous` and exact resume,
  so a wrong guess is felt through the physical buttons — the most-used surface on the device.

## Decision

### 1. Metadata comes from `mutagen`, behind a port

A `MediaProbe` port returns one probed file — duration, tags, embedded chapters, embedded artwork,
ReplayGain, fingerprint — with no library type crossing the boundary. The adapter uses **`mutagen`**.

It is the only credible option that covers what ADR 0009 § 4 actually demands: ID3, Vorbis comments
and MP4 atoms, MP4 chapter atoms, the FLAC `CUESHEET` block and ReplayGain tags, without decoding
audio. It is pure Python, has no build step on a Raspberry Pi, and reads headers only — so scanning a
few hundred files costs seeks, not decodes.

**`mutagen` is GPL-2.0-or-later.** ADR 0004's "no GPL linked into the application" constraint is *on
hold* (ADR 0006: nothing is distributed), so this is permitted today and is recorded here so the
decision is not rediscovered as a surprise. The exposure is bounded by construction: the dependency
lives in exactly one adapter module behind a port. If AQENO is ever published under a non-GPL licence,
that module is replaced — the fallback is named in § 5 below, not left to be researched then.

### 2. Discovery is an explicit scan, not a filesystem watcher

Media lives under configured **library roots**. The default root is `$XDG_DATA_HOME/aqeno/media/`;
further roots are Manager-tier settings.

A scan runs at startup and on explicit Manager request. *(Superseded by ADR 0028 § 1: preparation runs
on explicit request only. The rejection of a watcher below stands, and ADR 0028 § 6 leans on it — with
no watcher, the human trigger is itself the copy-completion boundary.)* There is **no `inotify`
watcher.** Content on
this device changes when an adult deliberately copies files onto it — a rare, human-initiated event
that pairs naturally with a "rescan" action. A watcher would add recursive watch descriptors on an SD
card, a debounce policy for half-copied files, and a second concurrent writer to the library, to
automate something that happens a few times a year. `AGENTS.md` § "Productive work only" decides this.

Scanning is **incremental**: a file whose size and modification time are unchanged since the last scan
is not re-probed.

### 3. Identity survives moves, renames and retagging

Each file gets a **fingerprint**: its exact byte size plus a hash of a 64 KiB window taken from the
middle of the file.

The midpoint matters. Tag editors rewrite the *header* — a header hash would change identity every
time someone corrects a title, which is precisely when identity must hold. Audio payload in the middle
of the file is what stays constant. A full-file hash would be correct too and is rejected on cost:
hashing a 40 GB library on an SD card is minutes of I/O per scan for no additional certainty.

A rescanned file matching a known fingerprint **is** that file, at a new path; the path is updated and
nothing else changes. A work keeps its `ContentId` when more than half of its files match files of a
known work — which survives renaming the folder, adding a bonus track or re-ripping one track.

**Nothing is ever deleted by a scan.** A work whose files have all disappeared becomes *unavailable*
and keeps its resume position and tag mappings (ADR 0007 § 3, `FAILURE_STATES.md` row 1 and rule 2).
Removing content is an explicit Manager action.

### 4. Ambiguous kind resolves towards long-form, and a Manager overrides it

ADR 0009 § 5 already concedes that a 40-minute Hörspiel and a 40-minute album are indistinguishable by
shape. A default is therefore unavoidable, and it should be chosen by **which error hurts**:

- Hörspiel misread as music → no exact resume. The child loses their place mid-story, every time.
- Album misread as audio drama → shuffle unavailable, and `Next` still moves to the next track.

The costs are not symmetric, and this is a bedtime device for a child. **When the signals are
ambiguous, ingestion chooses the long-form kind.** The inferred kind is always visible and always
overridable; an override is persisted against the `ContentId` and never re-inferred (ADR 0009 § 5).

A hand-editable `aqeno.toml` beside the media is accepted as an explicit declaration, ranking just
below a Manager override. A device without a keyboard needs a way to fix things over SSH — the same
argument that gave settings a TOML file in ADR 0007.

### 5. Scanning never blocks playback

*Superseded by ADR 0028 § 1 and § 3. The goal below — playback never waits for ingestion — is kept and
strengthened: preparation no longer runs at startup at all, and its results are no longer visible
incrementally. The reasoning recorded here is why "off the critical path" once seemed sufficient.*

Ingestion runs after `LOCAL_READY`, off the thread that serves input and playback, and commits its
results incrementally. Content already in the library is playable while a scan runs, which is what
`PLATFORM_CONTRACTS.md` § Readiness means by "later states may not unnecessarily block earlier local
functions". A first scan on an empty library is the one case where the surface is genuinely empty, and
that is `library_empty` — a calm screen, not an error (`FAILURE_STATES.md` row 11).

Named fallback for § 1: **GStreamer's `GstDiscoverer`** (LGPL, already a dependency via ADR 0003). It
gives duration and tags reliably, but its table-of-contents support does not cover the CUESHEET and
MP4-chapter cases, and it prerolls each file — a decode per file instead of a header read. It is the
replacement to reach for if the licence constraint returns, at a known cost in chapter fidelity.

## Alternatives considered

**`tinytag` (MIT).** No licence question at all, tiny, header-only. Rejected because it does not read
FLAC `CUESHEET` or MP4 chapter atoms, which is exactly the CD-ripped-Hörspiel case ADR 0009 § 4a
declares load-bearing. Choosing it would mean either no chapters for the most important content kind,
or writing a container parser by hand.

**Derive `ContentId` from a path or a path hash.** Simplest thing that works, and it is what most small
media players do. Rejected by ADR 0007 § 3, and for a concrete reason: the maintainer will reorganise
the media folder, and every resume position and NFC mapping in a child's library would silently reset.

**Full-file content hash as identity.** Rigorous. Rejected on I/O cost against no practical gain over a
size-plus-window fingerprint for identifying files a scan has already catalogued.

**One `ContentItem` per file, grouped later in the UI.** Rejected by ADR 0009 § 4 — grouping is a
domain fact that resume, `Next` and the tile surface all depend on, so it cannot live in presentation.

**A filesystem watcher for instant availability.** Rejected in § 2 as disproportionate; revisit only if
real use shows copying content is frequent.

## Consequences

**Easier.** Identity, availability and the tile surface all follow from one scan pass with one policy
document behind it. The library becomes reorganisable without loss, which is the property that makes it
safe to keep a child's progress for months (ADR 0009 § 2). The desktop run target gets real content
instead of fixtures wired into `__main__.py`.

**Harder.** AQENO acquires its first runtime dependency — until now `pyproject.toml` declared none, and
PySide6 and PyGObject come from system packages. `mutagen` is pip-installable and pure Python, so it is
a genuine dependency in the manifest, with its licence recorded per ADR 0004 § 2. Ingestion also needs
real fixtures: a multi-file rip, an `.m4b` with chapters, a FLAC with a `CUESHEET`, a mistagged file.
ADR 0009 already predicted that chapter handling is the part most likely to be wrong on real files.

**Constrained.** The persistence schema gains per-file fingerprints, an availability flag and a
last-seen timestamp, which is the project's first forward-only migration against a schema that already
holds data (ADR 0007 § 5). Kind inference lives in one place and returns a kind plus a reason; no other
module may guess. `application/` may walk the filesystem with `pathlib` — rule 1 of the layout permits
the standard library — but may not read audio bytes: probing is the adapter's job.

**Deliberately still open.** Podcast/RSS ingestion and radio-station entry are not scans of a
filesystem and are not covered here; they add Sources to the same identity model when their journeys
exist. Artwork placeholders are a presentation concern. Loudness normalisation stays where ADR 0009 § 6
left it — ingestion only *records* the ReplayGain tags it finds.
