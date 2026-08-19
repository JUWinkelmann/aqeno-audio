# Content Ingestion

**Date:** 2026-08-18, revised 2026-08-19 for ADR 0028 and ADR 0029
**Closes:** gap G14, together with ADR 0014.

ADR 0014 decides *how* content is discovered and identified. **ADR 0028 decides when that work runs
and when its result becomes visible. ADR 0029 decides what its metadata may claim.** This document
specifies all three precisely enough to implement without a second decision: the preparation pass, the
grouping and identity rules, the kind-inference table, chapter derivation, metadata resolution,
artwork resolution, playlist handling and what the library stores.
`docs/product/MEDIA_CONVENTIONS.md` says the same thing to an administrator in one page and must stay
true to §§ 3, 6, 7, 16, 18 and 21.

Vocabulary: a **work** is what becomes one `ContentItem` (ADR 0009 § 4). A **member file** is one
audio file belonging to a work. A **chapter** is one entry in `ContentItem.chapters` — a scene, track
or chapter depending on kind. Every work has at least one chapter. A **revision** is one published
generation of library membership (§ 16). A **candidate** is a revision under preparation, which no
Device surface can read.

The governing invariant, from ADR 0028 § 1:

> Device startup opens an already prepared revision. It never walks the media tree, probes a file,
> parses a playlist, resolves artwork or decodes an image — and no failure changes that.

## 1. Where media lives

| Setting | Default | Range / form | Tier |
|---|---|---|---|
| `library.roots` | `["$XDG_DATA_HOME/aqeno/media"]` | 1–8 absolute directory paths | Manager |
| `library.follow_symlinks` | `false` | boolean | Manager |

`AQENO_MEDIA_DIR` overrides the default root, alongside the existing overrides in ADR 0007 § 4, so
tests never touch real media. A configured root that does not exist is logged once and skipped — it is
not created, and it is not an error: a removed USB disk must not stop startup.

**`library.scan_on_startup` no longer exists.** It was removed by ADR 0028 § 1 rather than defaulted
to `false`, because a setting implies the behaviour is a choice. Preparation is always explicitly
triggered; boot is never a trigger.

A media root is an **authorised root**: the only region of the filesystem preparation may read, and
the boundary every resolved playlist path is tested against (§ 18).

Recognised extensions, case-insensitive: `.mp3` `.flac` `.ogg` `.opus` `.m4a` `.m4b` `.wav` `.aac`
`.wma`. Everything else is ignored silently, including artwork, `.cue`, `.m3u` and `aqeno.toml`, which
are read as *inputs* to a work but are never content themselves. Hidden files and directories
(leading `.`) are skipped.

## 2. The preparation pass

Preparation builds a **candidate revision**. Nothing it writes is visible to any Device surface until
§ 16 publishes it.

1. Open a candidate revision, seeded from the current published revision so unchanged work is reused
   (§ 19).
2. Walk each root depth-first. Symlinks are followed only if `library.follow_symlinks` is set; a
   directory already visited in this pass is never visited twice.
3. Partition the tree into **work candidates** by § 3.
4. For each candidate, probe member files that are new or changed — a file whose path, byte size and
   modification time all match the previous revision is not re-probed, and its stored fingerprint
   stands.
5. Resolve identity by § 4: an existing `ContentId`, or a new one.
6. Derive kind (§ 5), chapters (§ 6), artwork (§ 16) and the remaining fields (§ 7).
7. Write the work into the **candidate**, and continue.
8. After the walk, mark every work known to the previous revision whose files were all absent as
   unavailable (§ 8).
9. Validate the candidate (§ 17). On success it may be published; on failure it is discarded and the
   current revision is untouched.

Preparation is single-threaded, runs off the playback thread and off the startup path, and never holds
a transaction across a probe.

**Per-work commits are commits into the candidate, not exposure.** ADR 0014 § 5 committed each work
into the live library, which made a half-finished pass user-visible; ADR 0028 § 3 replaces that with
one atomic publication at the end. A pass interrupted by a power cut leaves an abandoned candidate,
not a smaller library.

**Copy-completion boundary (ADR 0028 § 6).** The explicit trigger is the boundary. As a secondary
defensive measure only, a file whose size or mtime changes during the pass is excluded from this
candidate and reported; it is picked up by the next preparation. This is best-effort and is not what
makes the model correct.

## 3. What becomes one work

Applied per directory:

- A directory containing **one or more audio files** is one work. Its subdirectories are evaluated
  independently and become their own works.
- A directory containing **only subdirectories** is a container — an artist, a series, a shelf. It
  produces no work of its own.
- Audio files lying **directly in a library root** are each their own single-chapter work. A root is
  never one work, however few files it holds.

There is no depth limit and no attempt to detect multi-disc sets in `CD1/ CD2/` subfolders. Two discs
become two works; a Manager can correct that when the management surface exists. Guessing wrongly here
would merge two unrelated works under one resume position, which is worse than showing two tiles.

## 4. Identity

**Fingerprint** of a file: `(size_bytes, blake2b-128 of the 64 KiB window starting at size_bytes // 2)`.
For a file smaller than 64 KiB, the window is the whole file. Both components must match.

Resolution order for a work candidate:

1. Fingerprint every member file. Look each up among stored member files.
2. If matching files belong to exactly one known work **and** they are more than half of that work's
   stored member files, the candidate **is** that work: keep its `ContentId`, its resume positions,
   its tag mappings and any kind override. Update paths, chapters and metadata.
3. If matches spread across several known works, or reach the majority for none, treat the candidate
   as new: generate a fresh `ContentId`.
4. A known work not matched in this scan is not touched here; § 8 decides its availability.

Consequences that are intended, and are testable as such:

- Renaming or moving a folder changes nothing but paths.
- Retagging every file changes nothing: the fingerprint window is audio payload, not the header.
- Re-encoding a file gives it a new fingerprint. Re-encoding a *minority* of a work's files keeps the
  work; re-encoding all of them produces a new item, and the old one becomes unavailable rather than
  disappearing.
- Two byte-identical copies of one file in different folders fingerprint identically. The first work
  claimed by rule 2 wins; the second is new. Duplicate media is a library-hygiene problem, not
  something ingestion resolves silently.

## 5. Kind inference

First matching rule wins. Each result is stored with the rule that produced it, so a Manager surface
can later show *why* — ADR 0009 § 5 requires the guess to be visible.

| # | Condition | Kind |
|---:|---|---|
| 1 | A stored Manager override exists for this `ContentId` | the override; stop |
| 2 | `aqeno.toml` in the work directory declares `kind` (§ 9) | as declared |
| 3 | Any member file is `.m4b` | `AUDIOBOOK` |
| 4 | Genre or album tag matches audiobook keywords: `hörbuch`, `audiobook`, `lesung`, `spoken word` | `AUDIOBOOK` |
| 5 | Genre or album tag matches drama keywords: `hörspiel`, `audio drama`, `radio play`, `radio drama` | `AUDIO_DRAMA` |
| 6 | Genre tag matches a music genre and the work has ≥ 5 chapters with mean duration < 8 min | `MUSIC_ALBUM` |
| 7 | Single chapter, duration < 10 min | `MUSIC_TRACK` |
| 8 | Everything else | `AUDIO_DRAMA` |

Keyword matching is case-insensitive and substring-based on the Unicode-casefolded tag value, so
`Kinder-Hörspiel` and `HÖRSPIEL` both match. The music genre list is a fixed constant in code, not a
setting.

Rule 8 is the deliberate asymmetry from ADR 0014 § 4: when nothing indicates otherwise, a work behaves
as long-form, which means exact resume, no shuffle, and `Next` moving one chapter. A misclassified
album loses shuffle; a misclassified Hörspiel would lose a child's place in the story.

`RADIO_STREAM`, `PODCAST_EPISODE` and `PERSONAL_RECORDING` are never inferred by a filesystem scan.
They arrive through paths this document does not cover.

## 6. Chapters

### Source, in descending order of trust (ADR 0009 § 4)

1. **Embedded chapters** of a single-file work — MP4 chapter atoms, ID3 `CHAP` frames. Start offsets
   come from the container. *(MP4 atoms not yet implemented — see § 15.)*
2. **FLAC `CUESHEET` block**, then an external `.cue` file in the work directory. Offsets are cue
   timestamps against the single audio file the cue references.
3. **A playlist** (`.m3u`, `.m3u8`) in the work directory naming member files. Its order is the chapter
   order; entries pointing outside the work directory are ignored.
4. **Track-number metadata** (`TRCK`, `tracknumber`, `trkn`), ascending, for multi-file works.
5. **Natural filename order** — digit runs compared numerically, so `Kapitel 2` precedes `Kapitel 10`.
   Non-numeric comparison uses the collation from ADR 0005, never a byte sort.

Rules 1–2 describe a single file cut into chapters; rules 3–5 describe several files. If a work has
both — a folder of files where one carries embedded chapters — the file-level order from 3–5 wins and
embedded chapters within a member file are ignored. Mixing the two produces a timeline nobody can
reason about.

Where track numbers are absent, duplicated or inconsistent across a work, rule 4 is discarded whole and
rule 5 applies. A half-trusted ordering is worse than a predictable one.

### Timeline

`Chapter.start` is the offset on the **item** timeline, per `RESUME_BEHAVIOR.md`. For multi-file works
it is the cumulative sum of preceding chapter durations; `Chapter.source` holds that chapter's file.
For single-file works it is the container offset and `Chapter.source` is `None`.

A member file whose duration cannot be determined breaks the cumulative timeline, so it is excluded
from the work (§ 10) rather than being given a guessed duration.

`ContentItem.duration` is the sum of chapter durations. A work always has ≥ 1 chapter; a single-chapter
work has `has_chapters == False` and `Next`/`Previous` fall back to the kind's skip step (ADR 0009 § 2).

## 7. Remaining fields

| Field | Source, in order |
|---|---|
| `title` | Admin override (§ 21) → `aqeno.toml` `title` → album tag **if not a placeholder** (§ 21) → work directory name, unless the work is a root-level single file → playlist `#EXTINF` title (§ 18) → filename stem → `Audio N` |
| `artwork` | the seven-rule chain in § 16 |
| `language` | Admin override → `aqeno.toml` `language` → language tag if not a placeholder → `None` |
| `kind` | § 5, rule 1 of which is the Admin override |

The directory name and the work title are used unchanged — no stripping of leading track numbers, no
title-casing. Cleverness here corrupts legitimate titles: `225 - Der Puppenmacher` is the title. A
**chapter** title may drop a leading track number, because a chapter's position is already carried by
its order (§ 21).

**Artwork is referenced by path and never copied into the database** (ADR 0007 § 3). A missing artwork
is not a failure — the Device UI renders AQENO's own fallback treatment, which is a presentation
concern and not specified here. § 16 specifies resolution, derivation and ownership.

**ReplayGain** track and album gain/peak tags are read and stored when present, even though
normalisation is not implemented (ADR 0009 § 6). Reading them costs nothing at scan time and having
them already there is the entire point.

## 8. Availability

`ContentItem` gains an availability state derived at scan time:

- **available** — at least one member file was present and probed in the last scan.
- **unavailable** — the work is known, and none of its member files were found under any root.

An unavailable work keeps its identity, resume position, tag mappings and metadata. It is shown dimmed
and remains selectable; pressing it produces silence, not a message (`FAILURE_STATES.md` rule 7). When
its files reappear — at any path — the next scan matches them by fingerprint and it becomes available
again with its position intact.

A work is **never deleted by a scan**, for any reason.

## 9. The `aqeno.toml` sidecar

Optional, one per work directory, hand-written, and untrusted input like every other file the user can
edit. Unknown keys are ignored; an invalid value is logged and the key falls through to inference.

```toml
title = "Die Kuh Lieselotte"
kind = "audio_drama"     # a ContentKind value
language = "de"
```

It ranks below a Manager override and above every heuristic. A malformed file never prevents the work
from being ingested — worst case the work is ingested entirely by inference.

## 10. Failures during preparation

No failure in this table aborts preparation or wakes the display. Every one of them is an **Admin
finding** carried on the `Operation` resource; none of them reaches the Device UI (ADR 0028 § 14).

| Condition | Effect | Code |
|---|---|---|
| File unreadable (permissions, I/O error) | excluded from its work, reported | `source_unreadable` |
| File parses but has no usable duration | excluded from its work, reported | `source_unreadable` |
| Container or codec unsupported by the probe | excluded from its work, reported | `codec_unsupported` |
| File changed size/mtime during the pass | excluded from this candidate, reported (§ 2) | `source_unstable` |
| Every file of a candidate excluded | no work created; a *known* work becomes unavailable (§ 8) | — |
| Root missing or unreadable | root skipped, reported once | — |
| Artwork fails to decode | fallback used, **work stays playable**, reported | `artwork_unreadable` |
| Several ambiguous folder images | fallback used, reported (§ 16 rule 6) | `artwork_ambiguous` |
| Playlist entry missing, outside a root, or foreign-absolute | entry omitted, reported (§ 18) | `playlist_entry_invalid` |
| Library empty after a published revision | calm empty surface, setup guidance for a Manager | `library_empty` |
| Storage read-only or full | **candidate fails; the current revision stays published** (§ 17) | `storage_unwritable` |

The last row is the one that changed with ADR 0028. Previously a scan on a full disk simply failed to
persist. Now it fails *the candidate*, which is a safe outcome by construction: the published revision
was never written to, and no source media is deleted to make room.

## 11. Persistence

The schema gains, as one forward-only migration (ADR 0007 § 5) — the first against a schema that may
already hold data:

- a member-file table: `content_id`, ordinal, path, `size_bytes`, `fingerprint`, `mtime`, indexed on
  `(size_bytes, fingerprint)` because that lookup runs once per file per scan;
- `available` and `last_seen` on content;
- `kind_inference_rule` on content, so an inferred kind can explain itself;
- ReplayGain gain/peak columns.

`Library` gains `find_by_fingerprint()`, `get_member_files()`, `mark_unavailable()` and member files
as an optional argument to the **existing** `save_content()` — not a second saving verb. Two verbs for
one operation shape is the defect that was removed from this port once already. Omitting the argument
leaves stored fingerprints untouched, so non-scan callers are unaffected. The port keeps its
storage-agnostic vocabulary: no `upsert`, no SQL nouns.

ADR 0028 adds a second forward-only migration:

- a **revision** table: generation number, state (`candidate | published | superseded`), created and
  published timestamps;
- a single-row **current revision** pointer;
- a revision column on content membership, so a work belongs to a named generation;
- derived-artwork columns beside the artwork reference: the cache identity that detects a changed
  source, and the prepared dominant colour (§ 16).

What deliberately gains **no** revision column: resume positions, tag mappings, favourites, audience
and access overrides, and profiles. They are keyed by `ContentId` and their lifecycle is the person's,
not the library's (ADR 0028 § 2). This is the property that makes publication safe, and it is worth a
named test rather than a comment.

## 12. Modules

| Module | Responsibility |
|---|---|
| `ports/media_probe.py` | `MediaProbe` protocol; `ProbedFile` value object (duration, tags, chapters, artwork, ReplayGain, fingerprint). No adapter type crosses it. |
| `application/ingestion.py` | The whole of §§ 2–8 and § 18: walking, grouping, identity, inference, chapter assembly, playlist parsing and path validation. Standard library only. |
| `adapters/metadata/mutagen_probe.py` | The only module importing `mutagen`. Reads headers and the fingerprint window. |
| `adapters/fakes/metadata.py` | A dict of path → `ProbedFile`, so the whole policy is testable without files. |

The separation ADR 0028 § 72 asks for is expressed as modules, not as one media god-object:

| Concern | Where |
|---|---|
| source transport (how bytes arrive) | Management API upload; a share or USB importer if one is ever decided |
| interpret/validate incoming media | `application/ingestion.py` |
| artwork resolution (which image) | `application/ingestion.py` — policy, no decoding |
| derived asset preparation (decode, resize, dominant colour) | an image adapter behind a narrow port; the only module that decodes an image |
| library build | `application/ingestion.py` writing a candidate |
| publication | the `Library` store — one transaction |
| device consumption | `application/device_ui.py` reading the current revision |
| playback | `application/playback.py` on the resolved `ContentItem` |

Directory walking with `pathlib` stays in `application/` — layout rule 1 permits the standard library —
but reading audio bytes is the adapter's job, including the fingerprint window. **Decoding an image is
likewise an adapter's job**, for the same reason and with the same boundary.

## 13. Invariants worth a named test

1. Moving a work's folder preserves `ContentId`, resume position and tag mapping.
2. Retagging every member file preserves `ContentId`.
3. Replacing a minority of member files preserves `ContentId`; replacing all of them does not, and the
   old work becomes unavailable rather than vanishing.
4. A folder of forty files is one item with forty chapters, and chapter starts are strictly increasing.
5. `Kapitel 10` sorts after `Kapitel 2`.
6. A work with no kind signal is ingested as `AUDIO_DRAMA` and therefore resumes exactly.
7. A Manager override survives a rescan and is never re-inferred.
8. An unreadable file removes itself from its work without failing the pass or the other works.
9. A preparation interrupted between two works leaves an abandoned candidate, not a changed library.
10. A read-only or full filesystem fails the candidate and leaves the published revision intact.

Added by ADR 0028:

11. **Startup opens the published revision and reads no media.** Given a prepared library, startup
    performs no directory walk, no probe, no playlist read, no artwork resolution and no image decode.
12. **A missing or corrupt index does not cause a scan.** It yields the retained previous revision, or
    an empty degraded library — never an emergency walk.
13. **A candidate is invisible.** Works written into a candidate are absent from every Device-facing
    read until publication.
14. **Publication is all-or-nothing.** No observable state shows part of N+1.
15. **A failed candidate leaves N byte-for-byte current**, including on a full disk.
16. **Publication adopts without restart**, and the adopting read is cheap.
17. **Publication does not interrupt playback**, does not requeue it and does not move focus.
18. **A work removed in N+1 keeps playing** until its session ends.
19. **Resume, tags and favourites survive republication** for an unchanged `ContentId`.
20. **A playlist entry cannot escape an authorised root**, including via `..`, a symlink or a foreign
    absolute path.
21. **Corrupt artwork leaves the work playable.**
22. **Artwork precedence is deterministic** for each rule of § 16.

Added by ADR 0029:

23. **An Admin override of any field survives preparation** and is never recomputed — title,
    language and artwork as well as kind.
24. **A placeholder album tag loses to the work directory name**; a useful album tag beats an ugly
    directory name.
25. **A work with no usable metadata is still playable**, titled from its filename or the fallback.
26. **An ambiguous folder asserts nothing**: no series, no arbitrary cover, fallback title,
    `needs_review` — and it still publishes.
27. **Chapter order is numeric**, not lexical, from track numbers or leading filename numbers.
28. **The Device UI performs no metadata resolution** and never exposes `needs_review` or provenance.

## 14. Deliberately out of scope

Podcast/RSS and radio entry (Sources without a filesystem), multi-disc merging, sophisticated
duplicate matching, loudness normalisation, and any Manager UI for corrections. Each attaches to this
model without changing it.

Left open by ADR 0028 rather than answered here: a playlist as its own browsable object (§ 18), how
bytes arrive for a file-manager copy (a network share is a candidate, not a decision), the
review-before-publish interface and its default, destructive storage cleanup, and the exact pixel
dimensions of derived artwork.

## 15. Implementation status

Implemented 2026-08-18 on `wip/content-ingestion` (commits `91588bb`, `5234c69`, `904e1ec`). Two parts
of this document are **not** yet true of the code, recorded here rather than left to be discovered:

- **§ 6 rule 1, MP4 chapter atoms.** `mutagen` has no reader for `chpl`/Nero chapter atoms, and
  writing one is a container-parsing project of its own. An `.m4b` still classifies as `AUDIOBOOK` by
  extension (§ 5 rule 3) and still plays; it falls back to a single chapter, so `Next` and `Previous`
  use the ±60/30 s skip step instead of chapter boundaries (ADR 0009 § 2 already defines that
  fallback). ID3 `CHAP` and the FLAC `CUESHEET` path are implemented. This is the gap to close first
  if real audiobooks arrive as `.m4b`.

One test limitation worth knowing when reading the suite: the ID3 `CHAP` fixture is written with
`mutagen` and read back with `mutagen`, because no second chapter-writing tool was available. It
proves the adapter's plumbing, not that it reads what other rippers produce. Retire it against a real
file when one exists.

## 16. Artwork resolution and derived assets

### Resolution

Resolved once during preparation. First match wins, and the extension order inside a rule is fixed as
written so two candidates never race. Matching is case-insensitive.

| # | Source | Notes |
|---:|---|---|
| 1 | explicit AQENO assignment for this `ContentId` | a Manager correction is never undone by the next preparation |
| 2 | embedded picture of the work's first chapter | |
| 3 | `<media-stem>.jpg` `.jpeg` `.png` `.webp` beside the file | the single-file work's own sidecar |
| 4 | `<playlist-stem>.jpg` `.jpeg` `.png` `.webp` | only when that playlist orders this work's files (§ 18) — the `Einschlafen.m3u` / `Einschlafen.jpg` case |
| 5 | `cover` → `folder` → `front` → `album`, each `.jpg` `.jpeg` `.png` `.webp` | conventional folder artwork |
| 6 | the one plausible image in the work directory | **only** when the count is exactly one |
| 7 | AQENO's generated fallback | presentation treatment, never a broken-image glyph |

Rule 6 does not guess: two or more ambiguous images fall through to rule 7 and raise
`artwork_ambiguous` for Admin. Rule 3 sits above rule 5 because a file-specific name is a stronger
statement of intent than a folder convention.

Artwork may belong to a work, a track, an album/series or — if a playlist ever becomes an object — a
playlist. Source images are never duplicated to express that; derivatives are shared where the cache
identity is the same.

### Derivation and ownership

Everything under AQENO's artwork directory is a **derivative** and is disposable (ADR 0028 § 9). The
originals are inputs and are never modified, moved, overwritten or deleted.

- A source image is decoded **once**, during preparation, with bounded dimensions and bounded memory,
  and stored at the size the Device UI actually displays. Only variants with a demonstrated use exist.
- The **cache identity** is the source artwork's identity plus its size and mtime. Audio files are
  never hashed to detect that a `cover.jpg` changed.
- The **dominant colour** is computed once from a downscaled sample and stored beside the derivative.
  It exists so the Device UI can place a cheap tinted ambience behind a cover without analysing an
  image at runtime. It is one colour, not an image-analysis subsystem.
- Clearing the derived cache is always safe: published metadata plus source media regenerate it.

**QML never resolves artwork.** It receives a resolved URI, a fallback kind and the prepared colour. It
does not search directories, inspect filenames, parse tags, choose between `cover.jpg` and
`folder.jpg`, resize anything or compute identity (ADR 0028 § 1).

## 17. Revisions, publication and hot swap

A **revision** is a generation of library membership, numbered monotonically. A **candidate** is one
under preparation; exactly one revision is **published** at a time; the one it replaced becomes
**superseded**.

**Publication** is a single transaction: mark the candidate published, move the current pointer, mark
the previous revision superseded. SQLite's atomic commit is the mechanism, so a reader always sees the
complete membership of exactly one revision, and a crash mid-publication leaves N or N+1 — never a
mixture.

**Validation** before publication is structural and cheap: the candidate's schema generation is
understood, its pointer targets exist, and every member work has at least one chapter and at least one
resolvable source. Validation does not re-probe media.

**Adoption** raises one in-process notification. Presentation re-reads the current revision at a safe
boundary — surface entry, or idle — never underneath an active rotation, and retains focus by
`ContentId` where the focused work is still a member. No notice is shown; new content simply exists.

**Retention and cleanup.** The current and the previous revision are retained, which is what makes
rollback possible when a new revision turns out to be unopenable. Superseded generations beyond that
are pruned by explicit or opportunistic maintenance — never as a startup prerequisite, never removing
the current revision, and never removing derived assets a retained revision still references.

**Startup** locates the current revision, opens it, validates it cheaply, exposes it and becomes ready.
Cost is a function of the prepared index, never of the collection. If the current revision cannot be
opened, the retained previous one is used; if neither opens, AQENO starts with an empty degraded
library and an Admin-visible repair requirement. **No path here scans media** (§ 13 invariant 12).

## 18. Playlists and path safety

`.m3u`/`.m3u8` are read as descriptions of **order and membership**, never as content carrying artwork
of their own.

Parsing rules, all of which are testable and none of which is claimed beyond what is implemented:

- Entries resolve **relative to the playlist's own directory**.
- `\` is accepted as a separator, so a playlist authored on Windows works.
- Text is read as UTF-8; undecodable bytes are replaced rather than failing the file.
- A line beginning `#` is a comment. `#EXTINF` contributes its title only, and only where present.
- A resolved entry is accepted **only if its fully resolved real path lies inside an authorised root**,
  so `..` segments and symlinks cannot escape.
- An **absolute path from the authoring machine** is not treated as a device path. It is rejected and
  reported; where a remap is safe and unambiguous a client may offer one, which is a client concern.
- A missing target is omitted and reported. It never becomes a visible broken entry.

Every rejection is an Admin finding (`playlist_entry_invalid`), never a Device UI condition. A playlist
path is untrusted input, not a filesystem capability.

**Not decided here:** a playlist whose tracks span several albums is not a work under ADR 0009 § 4 and
has no `ContentKind`. Making a curated cross-album sequence browsable is a product decision about
content kinds; ADR 0028 § 10 records it as open, and the artwork chain in § 16 is written so adding it
later changes nothing already decided.

## 19. Incremental preparation

Preparation is incremental; publication is atomic. Conflating the two is what makes atomicity sound
expensive.

A candidate is seeded from the current revision, and a work whose member files all match the previous
revision by path, size and mtime is carried over whole: fingerprints, metadata, chapters, artwork
derivative and dominant colour are all reused, and nothing is re-probed or re-decoded. Only changed,
new or vanished works cost anything.

This is the unchanged-file skip that § 2 step 3 has always specified. Under ADR 0014 it was cost
optimisation and was never implemented; under ADR 0028 it is **load-bearing**, because it is what stops
"publish a complete revision" from meaning "rebuild everything every time".

## 20. Resource bounds

Imported media is untrusted input, and preparation is where it is bounded:

- filesystem access stays inside authorised roots;
- image decoding is bounded in pixel dimensions and memory before a decode is attempted, so an absurd
  or hostile image cannot exhaust RAM;
- oversized metadata and artwork are rejected rather than stored;
- symlinks are followed only when `library.follow_symlinks` is set, and never out of a root;
- unusual Unicode in filenames is preserved, not normalised into a collision;
- archives are **not** supported, and are not made supported by this document.

## 21. Metadata resolution: overrides, placeholders, provenance and review

ADR 0029. The precedence table in § 7 is the contract; this section defines the four mechanisms it
depends on. All of them are Admin-facing — none reaches the Device UI (§ 22).

**Overrides.** `ContentItem.overrides: frozenset[str]` names the fields an Admin has set explicitly.
The member names are a closed set — `title`, `kind`, `language`, `artwork`. Preparation never computes
a field named there; it carries the stored value forward unchanged. `kind_overridden` is
`"kind" in overrides`. Because overrides live on the `ContentId`, they survive republication by the
same mechanism as resume positions (§ 17), including republication that *would* now infer something
different. Clearing a name returns the field to inference and is the only way back — including after
the source tags are repaired.

**Placeholders.** A tag value is treated as absent when, trimmed and lowercased, it is:

| Form | Values |
|---|---|
| empty | `""`, whitespace only |
| unknown | `unknown`, `unknown artist`, `unknown album`, `unknown title`, `untitled`, `no title` |
| generic medium | `audio cd`, `audio track`, `audio file` |
| numbered stub | `track`, `title`, `spur` or `titel` followed only by digits, with or without a separator |

That is the entire list, and it is a constant with a test per entry so that extending it is an argued
change. `Various Artists` is a real answer and is **not** a placeholder.

**Chapter titles.** Embedded title if not a placeholder → filename stem with a leading track number
removed → the raw stem. A leading number is `digits` optionally followed by `.`, `-`, `_` or a space,
removed only when something non-empty remains. This applies to chapters and never to work titles,
because a chapter's position is already carried by its order while a work's number is meaning.

**Provenance.** `title` and `artwork` each store a `MetadataSource`: `ADMIN`, `EMBEDDED`, `PLAYLIST`,
`FILESYSTEM` or `FALLBACK`. Enough for Admin to say *"Title from folder name"*. The existing
`kind_inference_rule` string continues to serve this purpose for kind and is not replaced.

**Review.** `needs_review: bool`, true only when the title reached the § 7 fallback, artwork was
ambiguous (§ 16), or playlist entries were rejected or missing (§ 18). Absent tags are not a review
reason, and neither is a placeholder that a convention resolved. **Review never blocks publication**
— only invalid media or a broken structural relationship does (§ 10).

## 22. What the Device UI receives

The device model exposes resolved values: title, chapter title, artwork, duration, position, kind,
availability. It does **not** expose `overrides`, `MetadataSource`, `needs_review` or any preparation
finding, and QML performs no resolution of its own — a QML file must never need to know whether a
title came from a tag or a folder. The device never renders `Metadata incomplete`, `ID3 missing` or
`Please review tags`; those are Admin concerns, and on the device a missing value becomes AQENO's own
fallback treatment.

## 23. Never written back

Preparation does not rewrite ID3 tags, rename source files, reorganise folders, replace embedded
artwork or modify M3U files. AQENO's resolved metadata is AQENO's, stored in its own library; the
source tree is read-only input. AQENO stores the fields it presents or acts on — not BPM, composer,
conductor, encoder settings, ID3 versions or arbitrary frames. It is not a tag editor, and there is
no online lookup, acoustic fingerprinting or AI inference in core resolution.
