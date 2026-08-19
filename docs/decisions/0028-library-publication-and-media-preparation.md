# ADR 0028 — Library publication: prepared revisions, atomic publication and artwork

**Status:** Accepted
**Date:** 2026-08-19
**Supersedes:** ADR 0014 § 2 (scan at startup) and ADR 0014 § 5 (incremental commit)
**Amends:** ADR 0007 § 5 (the library schema gains a revision generation)

## Context

AQENO must accept a real personal media collection. The target workflow is deliberately dull: an
administrator copies ordinary folders onto AQENO with an ordinary file manager, and the content
appears. Real collections are messy — mixed metadata quality, embedded and sidecar artwork, playlists
written on another computer, 4000 × 4000 covers, missing covers, broken covers.

Three properties of the current implementation contradict that goal, and they are contradictions
rather than gaps:

**1. Startup scans the media tree.** `library.scan_on_startup` defaults to `true`, and
`_open_process()` starts a thread running `run_scan()` on every boot: recursive traversal, a `mutagen`
probe per file, embedded-artwork extraction. ADR 0014 § 5 accepted this because the scan runs *off*
the critical path, so it does not delay `PLAYBACK_READY`. That trade answers a different question than
the one that now matters. Startup cost on a 20 000-file library still scales with the collection, on SD
card I/O, on a Pi 4, every single boot — for work whose result was already computed the last time.

**2. Results are committed per work, so the filesystem effectively *is* the library.** `run_scan()`
writes each work into the live library as it finishes it, and `DeviceUiState.refresh_library()` is
called when the pass ends. A child browsing during a 200-audiobook import would watch the library grow
underneath them, and a half-copied folder becomes visible content the moment its first file probes.
There is no boundary between *present on disk* and *visible to the product*.

**3. Nothing is atomic and nothing is versioned.** There is no generation identity, no candidate
state, and no way to fail a preparation without having already damaged the current library.

What is *already right* is more than what is wrong, and this ADR deliberately keeps all of it:

- `ContentId` is a UUID, never derived from a path (ADR 0007 § 3).
- A **fingerprint** — byte size plus a hash of a 64 KiB window from the middle of the file —
  recognises a file across moves, renames and retagging (ADR 0014 § 3). Identity already survives
  folder reorganisation, which is the hard half of this problem.
- A work is a `ContentItem` with chapters; forty MP3s are one item, not forty (ADR 0009 § 4).
- Resume positions, tag mappings, favourites and access rules are keyed by `ContentId` and nothing
  else. `PlaybackSession` holds the **resolved `ContentItem` in memory** (`self._item`) and builds its
  queue from `self._item.chapters`; it never re-reads the library mid-playback.
- Nothing is ever deleted by a scan; a work whose files vanish becomes *unavailable* and keeps its
  identity, position and mappings (ADR 0014 § 3).
- The Management API already owns import and scanning: `POST /api/v1/imports` streams an upload to an
  adjacent temporary file, fsyncs it and atomically renames it; `POST /api/v1/library/scans` returns an
  `Operation` with `queued | running | completed | failed`.

So this is not a new media architecture. It is a **publication boundary** placed into the one that
exists.

## Decision

### 1. The device plays a published revision; preparation happens outside the startup path

> **THE DEVICE PLAYS. THE PREPARATION TIER PREPARES.**

One honesty note, because the slogan invites a wrong picture: AQENO's Admin tier is **hosted on the
device**. There is no second machine, and this ADR does not invent one. The boundary is a *tier and a
trigger*, not a physical machine:

- Preparation is **explicitly triggered** (Manager action or an Admin client), never implied by boot.
- Preparation writes only into a **candidate** revision that no Device surface can read.
- Device startup and the Device UI never walk the media tree, probe a file, parse a playlist, resolve
  artwork or decode an image.

`library.scan_on_startup` is **removed**. Its replacement is not a different default — it is the
absence of the behaviour. Startup opens the current published revision and becomes ready.

### 2. A library revision is a generation of *membership*, not a copy of the library

The library gains a monotonically increasing integer **revision**. What is revisioned is which works
are members of the library and what their prepared presentation data is. What is *not* revisioned is
identity or anything a person accumulated:

| Lifecycle | Data | Revisioned |
|---|---|---|
| Published library | content membership, title, kind, chapters, sources, member files, artwork reference, prepared presentation data | **yes** |
| Device/user state | resume positions, tag mappings, favourites, audience/access, profiles | **no** — keyed by `ContentId` |

This split is the reason no store split is needed, and it is why publishing revision 43 cannot lose a
child's place in a story: the resume row is keyed by `ContentId` and never consulted the revision.

Rejected alternative: making a revision a whole database file swapped by pointer. It is atomic and
tempting, but resume, tags, favourites and profiles live in the same database and are written
*continuously while a candidate is being prepared*. A file swap would either discard those writes or
need a merge, and a merge is exactly the kind of quiet data loss this device must not have.

### 3. Publication is one transaction that moves a pointer

A single-row pointer names the current published revision. Publication is:

```
begin
  mark candidate N+1 published
  set current = N+1
  mark N superseded
commit
```

SQLite's commit is atomic and crash-safe, so at every observable instant a reader sees the complete
membership of exactly one revision. There is no window in which half of N+1 is visible, and a crash
mid-publication leaves either N or N+1 — never a mixture. This is the mechanism ADR 0007 already chose
for durability; nothing new is introduced to obtain atomicity.

Preparation may take minutes and may be interrupted, retried or abandoned. A candidate that never
publishes is invisible and disposable.

### 4. Hot swap, and never a restart

A successfully published revision is adopted without restarting the process, the service or the
device. The runtime responsibility is deliberately tiny: publication raises an in-process
notification, and the presentation state re-reads the current revision at a safe boundary. It is a
cheap read of already-prepared rows — never "now go and look at the 200 new audiobooks".

No IPC, no watcher, no event framework. Publication and the Device UI already live in one process, and
`DeviceUiState.refresh_library()` is already the refresh seam.

**Refresh boundary.** The library is re-read on surface entry or while idle, not underneath an active
interaction, and focus is retained by `ContentId` where the focused work still exists. A person
mid-rotation does not have the list mutate under their hand. There is **no** "library updated"
notice: new content simply exists the next time it is looked at (P19).

### 5. Publication never touches playback

Publication does not stop, restart, seek, requeue or re-volume anything, and it does not navigate or
steal focus. This holds by construction rather than by care: `PlaybackSession` owns the resolved
`ContentItem` and its chapter queue in memory.

The consequence is the edge case worth naming: **a work removed in N+1 keeps playing to its end.**
Membership decides discoverability, not the fate of a session already under way. After the session
ends, the work is simply no longer offered. A tag pointing at a work that is no longer a member
resolves to nothing and follows the existing missing-content behaviour — it is never silently
remapped to something else.

Source media is never deleted by AQENO (§ 7), so "do not delete media still in use" needs no
reference counter. Only AQENO's own derived artwork is collectable, and only under § 9.

### 6. On the manual import path, the completion boundary for a copy is the human, not a timer

A 4 GB folder arriving over a network share must never become visible at 500 MB. **For the manual
import path decided here** — the only one that exists — AQENO's boundary is **the explicit trigger
that already exists**: the administrator copies, then asks AQENO to prepare. ADR 0014 § 2 rejected a
filesystem watcher, and that rejection is what makes this simple — without a watcher there is nothing
racing the copy.

This is a property of *that path*, not of the model. **Every atomicity guarantee in this ADR comes
from the candidate-and-publication mechanism of §§ 2–5, not from who or what signals completion.** A
partial copy is safe because it lands in a candidate nobody can read, and the trigger only decides
*when* preparation starts. A future automatic import path — a share with a watcher, a drop folder, USB
— therefore does not break this ADR; it must supply its own completion boundary, at least as strong as
the human trigger and explicit rather than inferred. A transfer-complete signal, a sentinel or marker
file, or a session-close event all qualify. **The size/mtime stability check below may never be
promoted into that role** (see the note after the two mechanisms), and neither may a timer or a quiet
period: those are the fragile heuristics this section exists to avoid depending on.

Two supporting mechanisms, in descending strength:

1. **Client upload** — already atomic: temp file, fsync, rename. A partial upload is never a file.
2. **File-manager copy** — bounded by the human trigger. Preparation additionally requires each
   candidate file's size and mtime to be *stable across the pass*, and excludes a file that changed
   while being read.

That second check is a **defensive secondary measure, not the boundary**, and it is recorded as
best-effort precisely because § 8 of the brief is right that stability heuristics are fragile. It
catches an administrator who triggers preparation too early; it is not what makes the model correct.
If a copy is still in flight, the honest outcome is that its work is missing from the candidate and
appears after the next preparation.

A client or network disappearing mid-transfer therefore cannot expose a partial import: the published
revision was never touched.

### 7. Source media is non-destructive by default

AQENO does not recompress audio, rewrite tags, rename files, move folders, overwrite source images or
delete original artwork. Preparation is **read-only** with respect to everything a person supplied.

The presence of an optimised AQENO derivative never authorises deleting the original it came from.
Removing a work from the published library and deleting bytes from disk are different operations;
publication only ever does the former. A destructive storage-cleanup feature remains a separate
decision that does not exist.

### 8. Artwork resolution precedence

Resolved once during preparation, deterministically, first match wins:

| # | Source |
|---:|---|
| 1 | explicit AQENO assignment (Manager-set artwork for this `ContentId`) |
| 2 | embedded picture of the work's first chapter |
| 3 | sidecar matching the media basename — `<stem>.jpg` `.jpeg` `.png` `.webp` |
| 4 | sidecar matching the ordering playlist's basename, when one names this work's files |
| 5 | conventional folder artwork — `cover` → `folder` → `front` → `album`, each in jpg/jpeg/png/webp |
| 6 | the single plausible image in the work directory, if there is exactly one |
| 7 | AQENO's own generated fallback |

Extension order within a rule is fixed as written, so two candidates never race. Matching is
case-insensitive. Rule 6 applies only when the count is exactly one; several ambiguous images fall
through to the fallback rather than guessing, and the ambiguity is reported to Admin.

Rule 1 above rule 2 is the point of the whole chain: a Manager correction must not be undone by the
next preparation.

**Corrupt artwork does not invalidate playable audio.** An image that fails to decode falls through to
the fallback and is reported to Admin; the work stays playable. The fallback is a presentation
treatment in AQENO's own visual language, never a broken-image glyph or a filesystem icon.

### 9. AQENO owns its derived artwork; it does not own the originals

Source images are inputs. Everything under AQENO's artwork directory is a **derivative** and is
disposable: regenerable, invalidatable, replaceable, and safe to delete during controlled maintenance
without touching source media. Clearing the derived cache must never make a library unrecoverable —
published semantic metadata plus source media are the durable inputs.

Derivatives are keyed by a cache identity that detects a changed source cheaply: the source artwork's
identity plus its size and mtime. Multi-gigabyte audio is never hashed to discover whether a
`cover.jpg` changed.

A 4000 × 4000 JPEG is decoded once during preparation, bounded, and stored at the size the Device UI
actually displays. Exact pixel dimensions are an implementation constant chosen from the real UI, not
a number decided here, and only variants with a demonstrated use are generated.

**Prepared presentation data.** Preparation also records the artwork's dominant colour, once, beside
the derivative. This is what lets the Device UI place a cheap tinted ambience behind a cover without
analysing an image at runtime. It is one colour computed from a downscaled sample — not an
image-analysis subsystem.

Cleanup retains the current and the previous revision, runs only on explicit or opportunistic
maintenance, never as a startup prerequisite, and never removes the current revision.

### 9a. Image work uses Pillow, behind a port, and is optional

Deriving a display-sized cover and a dominant colour is the first time AQENO decodes an image at all,
and § 54 of the brief requires that decode to be *bounded* — an absurd or hostile file must not exhaust
RAM. That needs a real imaging library.

**Pillow**, behind an `ArtworkPreparer` port. It is MIT-CMU licensed, so unlike `mutagen` it raises no
question against ADR 0004; it ships ARM wheels, so there is no build step on a Raspberry Pi; and it has
the two things that make bounding cheap rather than theoretical: `Image.draft()` downscales a JPEG
*during* decode instead of after it, and `MAX_IMAGE_PIXELS` refuses a decompression bomb before it is
decoded.

Three constraints on how it is used:

- **Optional.** It is imported lazily inside the adapter. If Pillow is absent, artwork *resolution*
  (§ 8) still works completely and the source image is referenced directly; only the derivative and the
  dominant colour are skipped. A missing optional dependency must not cost AQENO its covers.
- **Never on the device path.** Preparation only. Nothing in startup, playback or the Device UI imports
  it, and the existing import-boundary test is the place that stays true.
- **Not Qt.** `QImage` would decode images with a dependency AQENO already has, and is rejected: it
  would couple media preparation to the UI toolkit and break the headless core's freedom from Qt.

Rejected alternative: computing a dominant colour by hand from raw bytes. Feasible for uncompressed
formats and not worth it for JPEG, PNG and WebP — it would mean writing three decoders to avoid one
permissively licensed dependency that is already packaged for the target.

### 10. Playlists are ordering inputs; a playlist as its own visible object is *not* decided here

`.m3u`/`.m3u8` are read as **descriptions of order and membership**, never as content with artwork of
their own. That is what they are today (`_playlist_order()` orders a work's chapters), and this ADR
extends it only as far as rule 4 of § 8: when `Einschlafen.m3u` names the files of a work,
`Einschlafen.jpg` beside it is a legitimate artwork candidate for that work.

**Deliberately left open.** A playlist that draws tracks from several albums is not a work under
ADR 0009 § 4 and has no `ContentKind`. Making a curated cross-album sequence a browsable object is a
*product* decision about content kinds and about what a child sees, not something ingestion may settle
by inventing a kind. It is recorded here as open rather than answered, and the artwork chain above is
written so that adding it later changes nothing already decided.

### 11. Playlist paths are untrusted input

A playlist entry is a string from another computer, not a filesystem capability.

- Entries resolve relative to the playlist's own directory.
- `\` is accepted as a separator so a Windows-authored playlist works.
- Encoding is UTF-8; undecodable bytes are replaced rather than aborting the file.
- `#` lines are comments; `#EXTINF` is read for its title only where present.
- After resolution, a path is accepted **only if it is inside an authorised media root**, tested on
  the fully resolved real path so `..` and symlinks cannot escape.
- An absolute path from the authoring machine is not silently treated as a device path. It is
  rejected and reported.
- A missing target is reported and omitted; it never becomes a visible broken entry.

An entry that fails any of these is an Admin finding, not a Device UI problem.

### 12. Failure never degrades into a scan

| Condition | Behaviour |
|---|---|
| Candidate preparation fails for any reason | N stays current, unchanged. No partial publication. Admin gets the detail. |
| Storage fills during transfer, artwork derivation or index build | preparation fails safely; N intact; **no source media is deleted to make room** |
| Crash during publication | either N or N+1 is current — the commit decides, not a recovery pass |
| Current revision cannot be opened | fall back to the retained previous revision if it opens; otherwise start with an **empty, degraded** library and an Admin-visible repair requirement |
| Index missing entirely | empty library, calm empty surface (`library_empty`) |

**No failure path triggers a media scan at boot.** Not a missing index, not a corrupt one, not an empty
one. Recovery is an Admin workflow. A device that "helpfully" rebuilds by walking 20 000 files on a
damaged SD card turns a repair into an outage, and ADR 0007 already refuses automatic wipes for the
same reason.

Startup is therefore bounded by the size of the prepared index, never by the size of the collection.

### 13. Preparation is incremental; publication is atomic

These are independent, and conflating them is what makes atomic publication sound expensive. A
candidate starts from the current revision's prepared data and re-does only what changed: unchanged
files keep their fingerprints, metadata, chapters and artwork derivatives. Publication is atomic
regardless of how much or little was recomputed.

The unchanged-file skip that CONTENT_INGESTION.md § 2 step 3 has always specified but never
implemented becomes load-bearing here, because it is what stops "atomic" from meaning "full rebuild".

### 14. Import problems belong to Admin; the Device stays calm

The Device UI shows no import progress, no counts, no "reading metadata", no "rebuilding index", and
no announcement that new content arrived. Unsupported files, broken audio, unreadable metadata,
corrupt covers, ambiguous folder images, missing playlist targets, foreign absolute paths, duplicate
paths and insufficient storage are **Admin findings**, carried on the existing `Operation` resource.

The Device UI consumes only valid published content. That is the whole reason the publication boundary
exists.

**Two admin policies must both remain possible** — publish automatically once a candidate validates,
or hold it for review and publish on approval. The candidate/publish split makes both expressible; the
review *interface* is not built here, and choosing a default is left to the Admin workflow rather than
settled by this ADR.

### 15. Ingestion is not messages, and not tags

Media ingestion decides what content exists. It is not Send to AQENO (ADR 0027) — different
lifecycle, privacy, retention and notification semantics — and infrastructure is shared only where it
is genuinely generic. It is also not NFC: a copied file is valid library content without any tag
assignment, and a tag only decides how existing content may be invoked (ADR 0013).

## Alternatives considered

**Keep the startup scan and make it faster.** The incremental re-probe skip would cut most of the
cost. Rejected as the wrong shape: it still makes startup a function of collection size, still exposes
works incrementally, and still offers no way to fail a preparation without damage. Cost was never the
only defect.

**A revision as a swapped database file.** Genuinely atomic via `os.replace` on a pointer, and it
gives free rollback. Rejected in § 2: user state shares the database and is written while a candidate
prepares, so publication would have to discard or merge those writes.

**A separate immutable library database plus a mutable state database.** The clean-architecture
answer, and the one to reach for if the library ever needs to be prepared on a different machine.
Rejected for now as disproportionate: it is a store split, a port split and a migration, to buy
atomicity that one SQLite transaction already provides.

**A filesystem watcher so content appears by itself.** Rejected again, as in ADR 0014 § 2: without a
watcher, the human trigger *is* the copy-completion boundary on the manual path, and no stability
heuristic has to be trusted. This is a rejection *for the path decided here*, not a permanent
prohibition on automatic import — § 6 states what a later automatic path must bring instead, and
nothing in §§ 2–5 depends on the answer.

**Rebuild the index at boot when it is missing or corrupt.** Superficially helpful. Rejected in § 12 —
it converts a repairable fault into an unbounded startup, on the hardware least able to absorb it.

**Derive a dominant colour in QML from the displayed image.** Rejected: it would put image analysis on
the presentation path, on a Pi 4, for a value that never changes once computed.

## Consequences

**Easier.** Startup becomes bounded and boring. A 200-audiobook import becomes a background
preparation with one visible moment — new content exists. Failure stops being dangerous: a candidate
can fail, run out of disk, or be abandoned without the working library noticing. The premium Device UI
gets artwork ambience for free at display time, because the colour was computed once.

**Harder.** The schema gains a revision generation and a pointer, which is a forward-only migration
against a schema holding real data (ADR 0007 § 5). Every read path that shows content to a person must
become revision-scoped, and a read path that forgets to be is a silent defect — it would show
candidate content. That risk is worth a named test rather than a comment. Preparation also acquires
image work, which is the first place AQENO decodes an image at all, and it must be bounded against a
hostile or merely absurd file.

**Constrained.** Imported media is untrusted input: path traversal, foreign absolute paths, malformed
metadata, malformed images and oversized artwork are all preparation's problem, and filesystem access
stays inside authorised roots. Preparation may not run on the startup path or the playback thread. No
new dependency is added for transport; a network share is a *candidate* for how bytes arrive and is
deliberately not decided here.

**Deliberately still open**, and none of it is invented to look complete:

- **A playlist as its own browsable object** (§ 10) — needs a content-kind decision.
- **How bytes arrive for a file-manager copy.** SMB is a candidate; its security, authentication,
  writable surface and operational cost are unevaluated. Only the intended import surface may ever be
  exposed, never the AQENO filesystem. USB import likewise attaches to the same preparation pipeline
  without duplicating library logic.
- **Whether import is ever automatic, and what its completion boundary is.** § 6 decides the boundary
  for the manual path only and deliberately leaves this open. An automatic path needs its own explicit
  boundary — not a timer, not the stability heuristic — and it may be added without changing §§ 2–5.
- **The review-before-publish interface**, and which policy is the default.
- **Destructive storage cleanup** beyond the non-destructive default.
- **Duplicate intelligence** beyond cheap exact-duplicate reporting.
- **Exact derivative dimensions**, pending measurement against the real UI.
