# Resume behaviour

**Date:** 2026-08-17
**Closes:** gap G12

Resume belongs to `(ContentItem, Profile)`. It does not belong to a file, NFC tag, tile or launch
method. Touch and NFC therefore read and update the same position, and changing a tag mapping does
not affect progress.

## Position

- A position is measured on the `ContentItem` timeline. For a multi-file work, a chapter-local
  engine position is offset by that chapter's start.
- All Sources of one item share that timeline. Source selection and fallback are resolution
  concerns; changing source does not create another resume record.
- Non-seekable sources and live radio neither read nor write resume positions.
- A negative or beyond-duration engine position is clamped before use.

## Starting and finishing

On launch, AQENO reads the profile's saved position and subtracts the configured rewind. The result
never goes below zero. Music shorter than ten minutes restarts according to ADR 0009; exact-resume
kinds use the saved position.

An item counts as finished when less than 30 seconds remain or at least 98 percent has played, as
defined by `CONFIGURATION_DEFAULTS.md`. A saved position in that region is ignored on the next
launch, which starts from zero. Reaching the natural end records the known item duration so the same
rule applies after restart.

## Persistence

While seekable content is playing, position is persisted every 10 seconds. It is also persisted
immediately on pause, stop, item change, profile change and orderly shutdown. Paused playback does
not produce periodic writes, and persistence never moves a stored position backwards.

The accepted loss after an unexpected power cut is at most 12 seconds. SQLite durability is defined
by ADR 0007; this document does not add another transaction policy.

## Deliberate boundary

This contract does not choose among multiple Sources or define retry/fallback order. Content
resolution and ingestion remain gap G14. The playback application receives the resolved Source and
keeps progress attached to the item identity.
