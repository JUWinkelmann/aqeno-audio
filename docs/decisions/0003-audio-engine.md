# ADR 0003 — Audio playback engine

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

`docs/implementation/PLATFORM_CONTRACTS.md` defines the audio port: load a resolved source,
play/pause/stop, seek where supported, volume, state and error callbacks, and no UI-specific
behaviour. Queue and next/previous logic sit above the engine, in the application layer.

The content types AQENO must serve (`PRODUCT_FOUNDATION.md` § 8) are broader than "play a file":
local audio, long-form audiobooks with reliable resume, podcast enclosures over HTTP, and internet
radio / HTTP streams. These have genuinely different behaviour — a stream has no meaningful seek or
duration — and `MVP.md` requires all three paths behind one content abstraction.

Two requirements constrain the engine specifically:

- **Gapless, low-latency response to physical controls.** `PLATFORM_CONTRACTS.md` targets wake input
  response < 500 ms, and volume must feel continuous under a rotary encoder.
- **The engine must never touch the display.** Buffering, track change and metadata updates must not
  produce any visual effect (`AGENTS.md`, `DISPLAY_BEHAVIOR.md`). An engine that assumes a UI is a
  poor fit.

Language is Python per ADR 0001; licensing constraints come from ADR 0004.

## Decision

**GStreamer 1.x via PyGObject, behind the audio port.**

- Use the **`playbin3`** element as the default pipeline for both files and network sources, so URI
  handling, demux, decode and sink selection are one code path. Local files and HTTP streams differ
  only in the resolved URI.
- **Plugin sets: `core`, `base` and `good` by default, plus whatever formats the maintainer's own
  library needs.** ADR 0004's licence-driven exclusion of `gst-plugins-ugly` and `gst-plugins-bad` is
  on hold because nothing is distributed, so **AAC / M4A / M4B is supported** — `.m4b` is a common
  audiobook container and excluding it would have been a real product cost. If AQENO is ever
  published or distributed, ADR 0004 § 5 and its patent reasoning return.
- **Volume is applied in the pipeline**, not by changing the system mixer, so the night volume
  ceiling and profile limits are enforced by AQENO rather than by ALSA state that other software
  could change.
- **The adapter translates GStreamer bus messages into port-level state and error callbacks.** No
  GStreamer type crosses the port boundary. `application/` must be testable against a fake audio
  adapter with no GStreamer installed.
- **Stream vs seekable capability is reported through the port**, so the application can express
  "radio has no resume position" as a domain fact rather than discovering it as a failure.
- **Gapless transitions between chapters of one work** are a port-level requirement, implemented via
  `playbin3`'s `about-to-finish` signal. See ADR 0009 § 4a: CD-ripped audio drama cuts scenes at
  arbitrary track boundaries, so a gap there is audible and wrong.

## Alternatives considered

**MPV via `python-mpv` / libmpv.** Very capable, excellent gapless and network handling, small API,
and genuinely tempting for the file and stream cases. Rejected primarily on licensing: libmpv is
LGPLv2.1+ but common builds link GPL components, and the practical distribution is frequently
GPL-effective, which conflicts with the commercial-path optionality in ADR 0004. Secondary concern:
it is a media *player* with player policy inside it, so more must be suppressed to keep the engine
free of presentation behaviour.

**FFmpeg / libav directly.** Maximum control and format coverage. Rejected as far too low-level: it
would mean writing the pipeline, sink management and clocking that GStreamer already provides, and
its licence configuration (LGPL vs GPL depending on build flags) needs the same care as GStreamer
without the offsetting benefit.

**Python-level libraries (`python-sounddevice`, `pygame.mixer`, `pyaudio`).** Simple for local
files. Rejected because they do not credibly cover HTTP streaming, network buffering, podcast
enclosures or robust seek in long-form audio — which is most of what the content model requires.

**MPD (Music Player Daemon) as a separate process.** Attractive robustness story: playback survives
an application crash. Rejected for the MVP because it imposes its own library and playlist model on
top of AQENO's content model, which conflicts directly with the `Content != Source != Trigger`
separation in `DOMAIN_MODEL.md`. GPLv2 is a further obstacle if it were linked rather than merely
invoked.

## Consequences

**Easier.** One pipeline for files, podcast enclosures and radio, which is exactly what "one content
library regardless of technical source" needs. Buffering, network resilience and format coverage are
mature and not AQENO's problem. GStreamer is headless by nature, so keeping playback visually silent
is the default rather than something to suppress.

**Harder.** GStreamer's error surface is verbose and technical, and the child-facing experience
requires the opposite (`USER_JOURNEY_KIDS_EARLY.md` § 8). The adapter must map bus errors onto a
small, calm, enumerated set of failure states — which is gap G08, and this ADR makes closing it a
prerequisite for the audio step of the slice rather than a later concern.

**Constrained.** Format coverage still needs an explicit failure path. Even with AAC available, some
file will eventually be unplayable — a broken container, an exotic codec, a DRM-protected file — and
that must produce a calm, enumerated failure state rather than a GStreamer error string. This is gap
G08, and it is a prerequisite for the audio step of the slice.

**Open verification (P2 feasibility spike).** On Reference hardware: import and pipeline-construction
cost against the boot budget; volume-change latency under rapid encoder rotation; seek accuracy and
resume precision in a long `.mp3` audiobook; behaviour when a stream drops mid-playback; and that no
bus message produces a display wake.
