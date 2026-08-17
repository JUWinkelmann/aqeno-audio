# ADR 0009 — Content kinds and their playback behaviour

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

`DOMAIN_MODEL.md` mentions "content kind" in one clause of `ContentItem` and never says what it
changes. `PRODUCT_FOUNDATION.md` § 5 assigns the physical buttons "Previous / contextual rewind" and
"Next / contextual skip" — and **"contextual" was never defined**. That single word hides the most
important behavioural difference in the product.

Music, audio drama (*Hörspiel*) and audiobooks are not variations of the same thing:

- A **song** is three minutes, restarts from the beginning, and lives in an album where `Next` means
  the next song.
- An **audiobook** is nine hours, is worthless without an exact resume position, must never be
  shuffled, and `Next` plausibly means the next chapter — or, for a child's single-file book with no
  chapters, nothing sensible at all.
- A **Hörspiel** sits between them: often one long track or a handful of scene tracks, resume matters,
  order is fixed, and it is the format most likely to be at the centre of a three-year-old's library.
- A **radio stream** has no position, no duration and no end.

Implementing `Next` without deciding this means inventing it, differently, in several places.

## Decision

### 1. `ContentKind` is a value object that carries a behaviour policy

Not a label, and not a set of `if kind == …` branches spread through the application. One kind, one
policy object, one lookup — the same capability-driven pattern the project already uses for
`Profile`.

```
MUSIC_TRACK · MUSIC_ALBUM · AUDIO_DRAMA · AUDIOBOOK · PODCAST_EPISODE · RADIO_STREAM · PERSONAL_RECORDING
```

### 2. Behaviour per kind

| Behaviour | Music | Audio drama | Audiobook | Podcast | Radio |
|---|---|---|---|---|---|
| `Next` | next track | next track/scene | next chapter, else **skip +60 s** | next chapter, else +60 s | **ignored** |
| `Previous` | restart track if > 3 s in, else previous track | same | previous chapter, else **skip −30 s** | same as audiobook | **ignored** |
| Resume position | remembered, but a track under 10 min restarts | **exact** | **exact** | **exact** | none |
| Resume retention | until superseded | months | **months** | months | n/a |
| Shuffle | permitted | **impossible** | **impossible** | impossible | n/a |
| At end of item | next track in collection | next track | next chapter | stop | n/a |
| At end of collection | **stop** | **stop** | **stop** | stop | n/a |
| Skip step | n/a | n/a | +60 s / −30 s | +60 s / −30 s | n/a |
| Tile in Kids Early | album = one tile | **one tile** | **one tile** | show/episode = one tile | one tile |

Asymmetric skip (+60 / −30) is deliberate: going back a little further than you skipped forward is how
people actually recover their place in a story.

### 3. Rules that hold across all kinds

- **Playback never auto-advances into unrelated content.** At the end of a collection it stops.
  `P12 AQENO does not optimise for engagement` is a product rule, and "next book starts automatically"
  is exactly the mechanic it forbids. This is also why there is no endless queue.
- **Shuffle is a capability of the kind, not a global setting.** For audiobooks and audio drama it
  must be *unavailable*, not merely off — a shuffled audiobook is a broken product, and a child will
  find any control that exists.
- **`Next` and `Previous` never leave the current item's collection.**
- Transport buttons behave identically with the display off. Their meaning comes from the kind, not
  from what is on screen (`DISPLAY_STATE_MACHINE.md` note 6).

### 4. A multi-file work is one item

A folder of forty MP3s that is one audiobook is **one `ContentItem` with forty chapters**, not forty
items. Kids Early shows very few large tiles; forty tiles for one book destroys that surface.

Chapter sources, in order of trust: embedded chapters (`.m4b`), a **FLAC `CUESHEET` block or an
external `.cue` file**, a playlist/index file, then filename and track-number ordering. Ordering is by
track metadata first, then natural filename sort — never byte sort, which puts `Kapitel 10` before
`Kapitel 2` (and see ADR 0005 on collation).

Tags come in two dialects and both must be read: **ID3** for MP3, **Vorbis comments** for FLAC and
Ogg, MP4 atoms for `.m4a`/`.m4b`. A ripped CD carries its structure in whichever one the ripper used.

### 4a. Gapless playback is required, not a refinement

A Hörspiel ripped from CD is usually **continuous audio cut into tracks at arbitrary points** — a
scene runs across a track boundary. A gap or click there is immediately audible and ruins the
listening experience in a way it never would between two songs.

Therefore: playback between chapters of the same work is **gapless**. GStreamer's `playbin3` supports
this by preparing the next URI on `about-to-finish` (ADR 0003), but it only happens if it is
implemented deliberately — the naive "wait for EOS, then load the next file" produces exactly the gap
this rule forbids.

This applies to every multi-chapter work regardless of format or kind. It does not apply between
separate items, where stopping is correct anyway (§ 3).

### 5. Kind detection is a guess, and the Manager overrides it

Tags lie constantly. Hörspiele are routinely tagged as music, audiobooks as podcasts, and German
retail rips as whatever the shop felt like.

- AQENO infers a kind from container, tags, duration and folder structure — a single 6-hour file is
  not an album, a 40-file folder of 3-minute tracks probably is.
- **The inferred kind is always visible and always overridable by a Manager**, and the override is
  persisted against the content identity.
- A wrong kind is a nuisance, not a failure: playback still works, only `Next` and resume feel wrong.

### 6. Loudness is a real problem for this device

Recorded here because it follows from the kinds and will otherwise be discovered at bedtime: **audio
drama has a wide dynamic range.** Quiet dialogue with sudden loud effects, played under the night
volume ceiling (`CONFIGURATION_DEFAULTS.md` § 3.2), means the dialogue is inaudible and the effects
are startling — the opposite of what a bedtime device should do.

Not MVP, but the right shape is known: optional loudness normalisation and gentle night-time dynamic
range compression, applied in the pipeline where the volume ceiling already lives (ADR 0003).
GStreamer provides the elements. Revisit after the first real bedtime use, which will settle it faster
than analysis.

Where files already carry **ReplayGain** tags — common in FLAC and Ogg via Vorbis comments — the
normalisation gain is free and needs no analysis pass. Read them during ingestion even before
normalisation is implemented, so the data is there when it is.

## Alternatives considered

**One uniform behaviour for everything.** Simplest, and defensible for an MVP. Rejected because
`Next` is a physical button a child presses constantly, and "next chapter" versus "next song" versus
"nothing" is not a refinement — getting it wrong makes the button feel broken.

**Kind as a free-text tag with behaviour decided in the UI.** Rejected: it puts playback semantics in
the presentation layer, which `AGENTS.md` forbids, and the display is off for most of these
interactions anyway.

**Infer behaviour from duration alone**, with no kind at all — long file means audiobook rules, short
file means music rules. Genuinely tempting, and it would get most cases right. Rejected because it
fails exactly where it matters: a 40-minute Hörspiel and a 40-minute DJ mix want opposite behaviour,
and the user has no way to correct it.

## Consequences

**Easier.** "Contextual skip" becomes a table instead of a judgement call, so it can be implemented
and tested without further decisions. Kids Early's tile surface stays small because multi-file works
collapse to one item. The no-auto-advance rule falls out of the model rather than needing a guard
somewhere.

**Harder.** Ingestion (gap G14) now has to detect kind, group multi-file works and extract chapters —
noticeably more than "scan a folder for audio files". Chapter handling is the part most likely to be
wrong on real files, so it needs fixtures built from real-world container shapes.

**Constrained.** `ContentItem` gains a kind and a chapter list; `DOMAIN_MODEL.md` needs updating.
Shuffle cannot be a global setting. No code branches on kind outside the policy lookup.

**Interaction with ADR 0005.** Kind is independent of content language: a German audiobook in an
English UI keeps German chapter titles, unsorted by English rules.
