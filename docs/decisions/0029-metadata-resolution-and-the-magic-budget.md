# ADR 0029 — Metadata resolution, media conventions and the Magic Budget

**Status:** Accepted
**Date:** 2026-08-19
**Amends:** ADR 0014 § 4 (an override is a set of field names, not a kind-only flag)
**Builds on:** ADR 0028 (preparation writes a candidate revision; publication is atomic)

## Context

AQENO must be pleasant to use with the collection a person already owns. Those collections carry
absent tags, wrong tags, `Track 01`, `Unknown Artist`, `Audio CD`, folder structures that say more
than the tags do, sidecar covers, playlists written on another computer, and CD rips from 2003.

Most of what this needs already exists and this ADR keeps it:

- A work is a `ContentItem` with ordered `Chapter`s (ADR 0009 § 4). Twenty MP3s in a folder are
  already **one** user-facing item with twenty technical segments, so the distinction between user
  content and technical segmentation is a solved problem, not a new one.
- `ContentId` is a UUID resolved by **fingerprint majority** (ADR 0014 § 3), never derived from
  title, artwork or path. Display metadata is already free to change without creating new content.
- Segment order already prefers order-bearing evidence: playlist, then valid track numbers, then a
  natural sort in which `10` follows `2` (`CONTENT_INGESTION.md` § 6).
- `aqeno.toml` beside the media is already an explicit declaration outranking every heuristic.
- Artwork precedence is already decided in ADR 0028 § 8 and is not restated here.

Two things are actually wrong, and one of them is a defect rather than a gap.

**1. An Admin correction does not survive preparation.** `update_metadata()` sets
`kind_overridden=True` when the kind changes, and § 4 rule 2 of the ingestion spec preserves it — so
**kind** survives. `title`, `language` and `artwork` have no such flag. Every preparation pass
recomputes them from the sidecar, the tags and the folder name and saves the result. An
administrator who corrects `Folge 225 - Puppenmacher` to `Der Puppenmacher` has that correction
silently reverted by the next import. `set_artwork()` is reverted the same way, which also
contradicts ADR 0028 § 8 rule 1, where an explicit assignment is supposed to win.

**2. A tag that exists is treated as a tag worth showing.** The title chain is
`aqeno.toml → album tag → directory name → filename stem`. For the single most common German
children's-audio layout the album tag is `Audio CD`, so a folder called `225 - Der Puppenmacher`
is presented to a child as **Audio CD**. The information needed to do better is right there in the
path, and no rule looks at it.

The risk in fixing this is worse than the defect: metadata inference is where products grow a
weighted-signal engine that is confidently wrong. This ADR therefore fixes both, and simultaneously
fixes the *ceiling*.

## Decision

### 1. The Magic Budget bounds automatic interpretation

`PRODUCT_FOUNDATION.md` P26 makes **accept messy, infer obvious, never guess** a product principle.
A rule may interpret media automatically only if it is deterministic, bounded, testable, and
explainable to an ordinary administrator **in one sentence**. Before any future inference rule is
added, all six answers must hold:

1. Which real user problem does it solve?
2. Is that problem common enough to justify permanent complexity?
3. Can the rule be stated in one sentence?
4. Is it deterministic — same inputs, same output, no ordering luck?
5. Can it produce a confidently *wrong* user-facing result?
6. Would a visible fallback or an Admin correction solve it more safely?

If 5 is yes, or 6 is yes, the rule is not added. **Wrong is worse than ugly:** showing
`Hörspiel 017` is a better failure than presenting the wrong episode of the wrong series.
Deleting a heuristic is preferred over documenting its exceptions.

### 2. An override is a set of field names, and it outranks everything

`ContentItem` gains `overrides: frozenset[str]`, holding the names of fields an Admin has set
explicitly — currently `title`, `kind`, `language`, `artwork`. Preparation **does not compute a
field listed there**; it carries the stored value across unchanged. `kind_overridden` is replaced by
`"kind" in overrides`, generalising ADR 0014 § 4's "persisted against the `ContentId` and never
re-inferred" from kind to every correctable field.

This is a set rather than four booleans because the rule is one rule, and a boolean per field
invites a fifth field to arrive without one. It is not a generic property bag: the member names are
a closed set, validated against the fields Admin can actually correct.

Because overrides are keyed by `ContentId` and `ContentId` survives moves, renames and retagging,
an override survives republication for free — it rides the same mechanism as resume positions
(ADR 0028 § 6). Clearing an override returns the field to inference, which is the only way back.

**EXPLICIT > INFERRED** is thereby structural, not a convention someone remembers to honour.

### 3. A tag that exists is not automatically a tag worth showing

A small closed set of **placeholder values** is treated as absent, matched case-insensitively on the
trimmed value:

- empty or whitespace-only;
- `unknown`, `unknown artist`, `unknown album`, `unknown title`, `untitled`, `no title`;
- `audio cd`, `audio track`, `audio file`;
- `track`/`title`/`spur`/`titel` followed only by digits, with or without a separator — `Track 01`,
  `Titel 3`, `track_07`.

That is the whole list. It is deliberately not a language-specific blacklist: these are the values
ripping software writes when it knows nothing, which is why recognising them is safe. `Various
Artists` is **not** a placeholder — it is a real answer. A tag equal to its own filename stem is
also not a placeholder; it is merely unhelpful, and the chain below reaches the same result anyway.

One sentence: *a tag that says only `Track 01`, `Unknown Album` or `Audio CD` is treated as if it
were missing.*

### 4. Presentation metadata has one documented precedence

For a work's `title`:

1. Admin override.
2. `aqeno.toml` `title`.
3. Album tag, **if it is not a placeholder** (§ 3).
4. Work directory name — unless the work is a single file lying directly in a library root, where
   the directory is a root and means nothing.
5. Playlist `#EXTINF` title, when a playlist orders the work.
6. Filename stem, unchanged.
7. `Audio` plus a stable ordinal — a visible, honest fallback.

Only step 3 changes existing behaviour, and it changes it in exactly one way: a placeholder album
tag no longer beats a real folder name. The directory name and the work title are still used
**unchanged** — no leading-number stripping, no title-casing — because `225 - Der Puppenmacher` is
a legitimate title and cleverness there corrupts it.

For a `Chapter` title: embedded title if not a placeholder → filename stem with a leading track
number removed → the raw stem. Stripping is safe *here* and not for work titles, because a chapter's
position is already carried by its order, so the number is noise rather than meaning. If stripping
leaves nothing, the raw stem is kept.

`language` gains the same placeholder-free treatment. `kind` inference (§ 5 of the ingestion spec) is
untouched.

### 5. Provenance is recorded, with the smallest vocabulary that explains a value

`title` and `artwork` each store the source that produced them, as a `MetadataSource`:
`ADMIN`, `EMBEDDED`, `PLAYLIST`, `FILESYSTEM`, `FALLBACK`. This is enough for Admin to say *"Title
from folder name"* or *"Cover from cover.jpg"*, which is the whole requirement. The existing
`kind_inference_rule` string stays as it is — it is finer-grained, already tested, and already
serves this purpose for kind.

No provenance framework, no per-field audit trail, no timestamps, and no provenance for fields
nobody needs to explain.

### 6. Review flags material ambiguity, and never blocks publication

`ContentItem` gains `needs_review: bool`, set during preparation when ambiguity **materially harms
the experience**, which is exactly three situations:

- the title reached step 7 of § 4 — AQENO has nothing to show but a fallback;
- artwork was ambiguous (ADR 0028 § 8: several plausible images, none conventionally named);
- a playlist referenced entries that were rejected or missing.

Absent tags are **not** a review reason. Neither is a placeholder tag that a convention resolved:
`225 - Der Puppenmacher/01.mp3` with `Track 01 / Unknown Artist / Audio CD` publishes clean and
silent. That is the difference between *"4 of 200 items may need your attention"* and *"please
repair 437 ID3 fields"*.

Review never blocks publication. Presentation imperfection is not corruption; only invalid media or
a broken structural relationship blocks (ADR 0028 § 7). Flagged content imports, plays, and can be
assigned to a tag and corrected later.

`needs_review` is a boolean and not a state machine: `RESOLVED`/`INFERRED`/`OVERRIDDEN` are already
derivable from § 5's provenance plus `overrides`, so a parallel enum would be a second
representation of facts already stored. No confidence score is introduced — there is no workflow
that would consume one, and a float invites a threshold nobody can defend.

### 7. Grouping stays as it is, and series is not inferred

Two of this task's requirements contradict each other and the conflict is resolved explicitly.
*"Do not expose a ripped audiobook as twenty unrelated items"* requires grouping a folder;
*"do not group files merely because they share a directory"* forbids it. The existing rule —
**a directory containing audio files is one work; its subdirectories are their own works; files
directly in a root are each their own work** (`CONTENT_INGESTION.md` § 3) — is kept unchanged. It is
one sentence, deterministic, and the *only* reason a twenty-file audiobook works at all.

The protection an ambiguous folder actually needs is not fewer groups; it is fewer *claims*. For
`Import/audio1.mp3, audio2.mp3, holiday.jpg, scan.jpg` AQENO produces one playable work with a
fallback title, AQENO's own fallback artwork — never `holiday.jpg`, because ADR 0028 § 8 requires a
single plausible image — no series, and `needs_review`. Nothing about the folder is asserted.

**Series is not inferred from the parent directory.** It fails test 5 of § 1:
`Hörspiele/Benjamin Blümchen/Folge 12/` yields the right answer while `Import/225 - Der
Puppenmacher/` yields `Import`, and both look identical to a rule. AQENO has no series field today,
and the presentation `Die drei ??? / Der Puppenmacher / Folge 225` therefore remains unreachable.
The in-budget route is an explicit `aqeno.toml` `series` key plus an Admin field, which is a Device
UI information decision (`DEVICE_UI_PRINCIPLES.md`) and not a metadata one — so it is recorded here
as open rather than implemented.

### 8. The Device UI receives resolved metadata only

QML renders `title`, `chapter`, artwork and progress. It never learns whether a title came from a
tag or a folder, whether tags were poor, whether grouping was inferred, or that `needs_review`
exists — `needs_review` and provenance are Admin-facing and are not exposed on the device model.
The device never shows `Metadata incomplete`, `ID3 missing` or `Please review tags`; a child or an
older user sees resolved metadata or a calm fallback. This is enforced by an existing import-boundary
test plus a device-model test, not by intention.

### 9. Non-destructive, offline, deterministic

AQENO's resolved metadata is its own. Preparation never rewrites ID3 tags, renames source files,
reorganises folders, replaces embedded artwork or edits M3U files. AQENO is not a tag editor: it
stores the fields it presents or acts on, and not BPM, composer, conductor, encoder settings or
arbitrary ID3 frames.

Resolution is reproducible: identical sources, overrides and resolver behaviour give identical
results. No online lookup, no acoustic fingerprinting, no AI inference is part of core resolution —
core works offline. A future optional provider must behave as a *suggestion* requiring Admin
acceptance, which the override mechanism of § 2 already accommodates without change: an accepted
suggestion is simply an Admin override.

Inference semantics may change in a later version. Because a published revision stores resolved
values rather than recomputing them at read time (ADR 0028), an update cannot silently rename
existing items — new semantics apply when media is next prepared, and overridden fields are immune.
No migration framework is introduced for this.

## Alternatives considered

**Leave the album tag ahead of the folder name.** Honest, and it presents `Audio CD` to a child for
the most common layout in the target collection. Rejected: the fix is one placeholder test.

**Score metadata quality and pick the highest.** A confidence engine. Rejected under § 1 — no
workflow consumes a score, and the threshold would be indefensible.

**Infer series from the parent folder.** Rejected in § 7: right often enough to be trusted, wrong in
a way the user cannot see.

**Infer episode numbers from `225 - …` or `Folge 12`.** A release-name parser. It would be wrong on
`4 Freunde`, `2 Jahre später`, box-set numbering and any collection numbered per box. Rejected: the
number is already visible inside the title AQENO shows.

**Detect multi-disc sets in `CD1/ CD2/`.** Already rejected by `CONTENT_INGESTION.md` § 3 for the
same reason — merging two works under one resume position is worse than two tiles.

**Fuzzy duplicate matching, cover web search, automatic file renaming, filesystem reorganisation,
a full tag editor.** All out of scope, and recorded as out of scope rather than deferred.

**A `MetadataResolver` service class with pluggable rules.** The resolution chain is six ordered
steps in one function. A plugin seam would be the abstraction this repository has refused
repeatedly, and it would make the precedence unreadable — which is the one property that must stay
obvious.

## Consequences

- An Admin correction is permanent until cleared. This is the point, and it means a correction also
  survives *the source being fixed*: an administrator who repairs the ID3 tags of an
  Admin-titled work will not see the repaired tag take effect. Clearing the override is the
  documented way to reconsider, and it is one action.
- Placeholder recognition is a value judgement encoded in a constant. A person whose album is
  genuinely called `Unknown` loses to their folder name. Acceptable, and correctable.
- The list will attract additions. It is a closed constant with a test per entry precisely so that
  extending it is a visible, argued change and not a quiet append.
- `Die drei ??? / Der Puppenmacher / Folge 225` stays unreachable until a series decision is taken.
  A folder-derived title is the honest interim result.
- Existing libraries are unaffected in identity. Some titles change on the next preparation, from a
  placeholder to a folder name — which is the improvement, and it cannot touch resume state.

## Deliberately still open

- A `series` field, its `aqeno.toml` key, its Admin field and whether the Device UI shows it (§ 7).
- Whether an Admin can clear an override from the Device UI, or only from Admin. Assumed Admin only.
- Where `needs_review` surfaces in Admin beyond the existing preparation findings (ADR 0028 § 7).
