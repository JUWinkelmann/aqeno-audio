# Content Ingestion

**Date:** 2026-08-18
**Closes:** gap G14, together with ADR 0014.

ADR 0014 decides *how* content is discovered and identified. This document specifies it precisely
enough to implement without a second decision: the scan pass, the grouping and identity rules, the
kind-inference table, chapter derivation and what the library stores.

Vocabulary: a **work** is what becomes one `ContentItem` (ADR 0009 § 4). A **member file** is one
audio file belonging to a work. A **chapter** is one entry in `ContentItem.chapters` — a scene, track
or chapter depending on kind. Every work has at least one chapter.

## 1. Where media lives

| Setting | Default | Range / form | Tier |
|---|---|---|---|
| `library.roots` | `["$XDG_DATA_HOME/aqeno/media"]` | 1–8 absolute directory paths | Manager |
| `library.scan_on_startup` | `true` | boolean | Manager |
| `library.follow_symlinks` | `false` | boolean | Manager |

`AQENO_MEDIA_DIR` overrides the default root, alongside the existing overrides in ADR 0007 § 4, so
tests never touch real media. A configured root that does not exist is logged once and skipped — it is
not created, and it is not an error: a removed USB disk must not stop startup.

Recognised extensions, case-insensitive: `.mp3` `.flac` `.ogg` `.opus` `.m4a` `.m4b` `.wav` `.aac`
`.wma`. Everything else is ignored silently, including artwork, `.cue`, `.m3u` and `aqeno.toml`, which
are read as *inputs* to a work but are never content themselves. Hidden files and directories
(leading `.`) are skipped.

## 2. The scan pass

1. Walk each root depth-first. Symlinks are followed only if `library.follow_symlinks` is set; a
   directory already visited in this scan is never visited twice.
2. Partition the tree into **work candidates** by § 3.
3. For each candidate, probe member files that are new or changed — a file whose path, byte size and
   modification time all match the last scan is not re-probed, and its stored fingerprint stands.
   *(Not yet implemented — see § 15.)*
4. Resolve identity by § 4: an existing `ContentId`, or a new one.
5. Derive kind (§ 5), chapters (§ 6) and the remaining fields (§ 7).
6. Write the work to the library and continue. **Results are committed per work, not per scan**, so a
   scan interrupted by a power cut leaves a smaller library, never a corrupt one.
7. After the walk, mark every previously-known work whose files were all absent as unavailable (§ 8).

The scan is single-threaded, runs off the playback thread, and yields the library connection between
works. It never holds a transaction across a probe.

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
| `title` | `aqeno.toml` `title` → album tag → work directory name → filename stem |
| `artwork` | embedded picture of the first chapter → `cover.*`, `folder.*`, `front.*` in the work directory (jpg/jpeg/png/webp) → `None` |
| `language` | `aqeno.toml` `language` → language tag → `None` |
| `kind_overridden` | `True` only for rule 1 of § 5 |

The directory name is used as a title unchanged — no stripping of leading track numbers, no
title-casing. Cleverness here corrupts legitimate titles, and a Manager can rename.

**Artwork is referenced by path and never copied into the database** (ADR 0007 § 3). Embedded artwork
is extracted once into `$XDG_DATA_HOME/aqeno/artwork/<content-id>.<ext>` and referenced from there; the
extraction is skipped when the file already exists and the work is unchanged. A missing artwork is not
a failure — the Kids Early surface renders a calm placeholder, which is a presentation concern and not
specified here.

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

## 10. Failures during a scan

No failure in this table aborts the scan or wakes the display.

| Condition | Effect | Code |
|---|---|---|
| File unreadable (permissions, I/O error) | excluded from its work, logged | `source_unreadable` |
| File parses but has no usable duration | excluded from its work, logged | `source_unreadable` |
| Container or codec unsupported by the probe | excluded from its work, logged | `codec_unsupported` |
| Every file of a candidate excluded | no work created; a *known* work becomes unavailable (§ 8) | — |
| Root missing or unreadable | root skipped, logged once | — |
| Library empty after a completed scan | calm empty surface, setup guidance for a Manager | `library_empty` |
| Storage read-only or full | scan runs, results are not persisted; degraded mode per ADR 0007 § 6 | `storage_unwritable` |

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

## 12. Modules

| Module | Responsibility |
|---|---|
| `ports/media_probe.py` | `MediaProbe` protocol; `ProbedFile` value object (duration, tags, chapters, artwork, ReplayGain, fingerprint). No adapter type crosses it. |
| `application/ingestion.py` | The whole of §§ 2–8: walking, grouping, identity, inference, chapter assembly. Standard library only. |
| `adapters/metadata/mutagen_probe.py` | The only module importing `mutagen`. Reads headers and the fingerprint window. |
| `adapters/fakes/metadata.py` | A dict of path → `ProbedFile`, so the whole policy is testable without files. |

Directory walking with `pathlib` stays in `application/` — layout rule 1 permits the standard library —
but reading audio bytes is the adapter's job, including the fingerprint window.

## 13. Invariants worth a named test

1. Moving a work's folder preserves `ContentId`, resume position and tag mapping.
2. Retagging every member file preserves `ContentId`.
3. Replacing a minority of member files preserves `ContentId`; replacing all of them does not, and the
   old work becomes unavailable rather than vanishing.
4. A folder of forty files is one item with forty chapters, and chapter starts are strictly increasing.
5. `Kapitel 10` sorts after `Kapitel 2`.
6. A work with no kind signal is ingested as `AUDIO_DRAMA` and therefore resumes exactly.
7. A Manager override survives a rescan and is never re-inferred.
8. An unreadable file removes itself from its work without failing the scan or the other works.
9. A scan interrupted between two works leaves a consistent, smaller library.
10. A read-only filesystem produces a scan that plays but does not persist.

## 14. Deliberately out of scope

Podcast/RSS and radio entry (Sources without a filesystem), multi-disc merging, duplicate detection,
artwork placeholders, loudness normalisation, and any Manager UI for corrections. Each attaches to this
model without changing it.

## 15. Implementation status

Implemented 2026-08-18 on `wip/content-ingestion` (commits `91588bb`, `5234c69`, `904e1ec`). Two parts
of this document are **not** yet true of the code, recorded here rather than left to be discovered:

- **§ 2 step 3, the incremental re-probe skip.** Every scan currently re-probes every file. Identity,
  availability and fingerprints are all still correct — this is cost, not correctness, and the scan
  runs off the startup path (ADR 0014 § 5), so nothing user-visible waits on it. It becomes worth
  doing when a real library is large enough to measure.
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
