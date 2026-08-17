# Documentation Gaps

**Date:** 2026-08-17
**Scope:** review of all existing documentation against what
`docs/implementation/FIRST_VERTICAL_SLICE.md` requires in order to be implementable.

## Summary

The documentation is unusually strong on **product intent** — principles, dark-room requirement,
role model, display behaviour, hardware philosophy. It is close to zero on **implementation
determinism**: nothing here tells an implementer what to build with, what values to use, or what
the state machines actually do.

The consequence is specific: `FIRST_VERTICAL_SLICE.md` is declared the implementation target, but
it cannot be implemented without inventing decisions that `AGENTS.md` forbids inventing.

Counts: **7 blocking** (1 closed), **7 important**, **8 hygiene**.

---

## Blocking — the vertical slice cannot start until these are closed

### G01 — No technology decisions exist, and no ADRs at all
`docs/decisions/` contains only the template README. `ARCHITECTURE.md` § "Decision still open"
lists SBC, frontend framework, playback engine, local database, remote architecture, packaging and
licence as unlocked. `AGENTS.md` requires an ADR before any of them is fixed.

Needed as ADRs before code, at minimum:
1. implementation language and runtime;
2. UI stack for the Kids Early surface (and how it runs on the Pi display);
3. audio playback engine behind the audio port;
4. local persistence mechanism and its atomicity story;
5. the local API / event channel between application core and UI;
6. test framework and how hardware ports are faked.

Without these there is no meaningful way to delegate implementation to anyone.

### G02 — Not a version-controlled repository — **CLOSED 2026-08-17**
The directory was not a git repository. Now initialised on `main` with remote
`git@github.com:JUWinkelmann/aqeno-audio.git`. The nine original documents are committed as a
single baseline; their pre-repository history is gone. See `MISTAKES.md` M-001.

### G03 — No repository layout, build or run instructions
No directory structure for the layers in `ARCHITECTURE.md`, no module naming, no dependency
manifest, no "how do I start it", no "how do I run the tests". `CLI_START.md` asks the agent to
produce a file/module plan — meaning the layout is currently expected to be improvised per
session, which guarantees drift.

### G04 — Display state machine is described but not specified
`DISPLAY_BEHAVIOR.md` lists five states and a set of prose rules. There is no transition table.
Undefined today:
- which events cause which transition, and which events are explicitly ignored;
- what happens on `WakeRequest` while `AMBIENT`, or while Night policy is active;
- whether `DIM` is reachable at all in Kids Early;
- what `SETUP` may interrupt, and how it is exited;
- precedence when Night policy, Ambient schedule and an explicit wake conflict.

This is the highest-value gap to close: the slice's items 7–9 and its dark-room definition of done
are all this state machine, and prose rules will be interpreted differently by every implementer.

### G05 — No concrete configuration values anywhere
The documents consistently say "short configurable timeout", "night-time volume ceiling",
"sleep timer" without a single number. Needed as defaults (with allowed ranges):
- inactivity timeout to `OFF` per profile;
- `DIM` timeout if `DIM` is used;
- night volume ceiling, and the units volume is expressed in;
- volume step per encoder detent;
- sleep-timer default;
- how often resume position is persisted;
- how long a wake stays `INTERACTIVE` before returning to `OFF`.

`PLATFORM_CONTRACTS.md` gives precise performance targets, which shows the project is willing to
commit to numbers — these are simply missing.

### G06 — Semantic input bus and simulator are unspecified
Slice step 4. `PLATFORM_CONTRACTS.md` defines the seven event types but not the bus: delivery
semantics, ordering, whether `VolumeDelta` coalesces, whether events are queued while `BOOTING`.
The simulator has no interface at all — keyboard mapping, CLI, socket, all undefined, though the
slice requires keyboard emulation of Volume/Play-Pause/Next/Previous and a simulated NFC UID.

### G07 — Local API / event channel is unspecified
Slice step 6 is "local API/event channel" with zero further description. Whether the UI is
in-process or a separate process is the single most consequential unmade decision after language
choice: it determines the whole shape of the codebase, and it is also a security boundary
(`AGENTS.md` forbids unauthenticated management interfaces).

---

## Important — needed before the slice's definition of done can honestly be met

### G08 — No failure taxonomy or calm-state specification
`USER_JOURNEY_KIDS_EARLY.md` § 8 requires "a calm, recoverable state" with no technical language.
Not implementable as written. Needed: enumerated failure cases (file missing, unreadable audio,
stream unreachable, unassigned NFC tag, empty library, storage full, no audio device), and for
each — child-facing representation, whether audio continues, whether the display may wake, and
what is logged. This is also the boundary where a weaker implementer will leak stack traces into
the UI.

### G09 — Persistence has a requirement but no design
`PLATFORM_CONTRACTS.md` requires atomic persistence and "unexpected power loss must not corrupt
the library". Undefined: file locations, on-disk format, write strategy, schema versioning and
migration, what is recovered vs discarded after a crash, and behaviour on a read-only or full
filesystem. Power-loss durability on an SD-card-based Pi is a real engineering constraint, not a
detail.

### G10 — Logging is required but unspecified
"Structured local logs without telemetry" (`MVP.md`) and "structured logs contain enough detail to
diagnose failures" (slice DoD). Undefined: format, levels, destination, rotation and retention,
and — given `AGENTS.md`'s privacy rules and child-data sensitivity — what must **never** be
logged. Retention defaults matter here because "default to minimum retention" is a stated rule.

### G11 — No test strategy
`AGENTS.md` lists eight invariants to protect. Nothing maps them to test layers, says how ports are
faked, how the dark-room and offline scenarios are automated, where test audio fixtures come from
(and their licence), or whether CI exists. "Offline smoke test passes" and "dark-room test passes"
are DoD items with no defined mechanism.

### G12 — Resume semantics are imprecise
Reliable resume is a headline capability. Undefined: whether resume is per ContentItem or per
ContentItem+Profile; tolerance in seconds; behaviour for streams and live radio, which have no
meaningful position; when an item counts as finished; what happens when the same content is
reachable through two Sources; and how position survives a hard power cut.

### G13 — Readiness states lack entry/exit criteria
Six states in `PLATFORM_CONTRACTS.md`, plus "later states may not unnecessarily block earlier local
functions" — but no definition of what completes each state, what is allowed to fail without
blocking, what the UI shows during each, and what happens to input events that arrive before
`PLAYBACK_READY`. "Unnecessarily" is not testable, yet the slice DoD depends on it.

### G14 — Content ingestion is undefined
The slice needs three local items and a library. Undefined: where media lives on disk, how it is
discovered (scan, watch, manual add), where metadata and artwork come from, how ContentItem
identity is derived and kept stable when a file moves or is re-tagged, and what happens to a
missing file that still has a resume position.

---

## Hygiene — record, fix cheaply, do not let them rot

### G15 — Accessibility is declared architecture but has no specification
`AGENTS.md`: "Accessibility and reduced-complexity modes are product architecture, not cosmetic
themes." No document defines contrast, touch-target size, motion reduction, audio feedback, or
what AQENO Easy actually needs. Given the Easy product line, this will become blocking later —
cheaper to sketch now than to retrofit.

### G16 — Roadmap phase contradicts the implementation documents
See `MISTAKES.md` M-003. `ROADMAP.md` says P0 with P1/P2 unstarted and MVP unfrozen; `MVP.md` and
`FIRST_VERTICAL_SLICE.md` say otherwise. Fix by stating in `ROADMAP.md` that an implementation
spike is deliberately running ahead of discovery, and why.

### G17 — Section numbering defects in `PRODUCT_FOUNDATION.md`
Two sections numbered `## 12` ("Startup, wake and perceived readiness" and "Hardware philosophy");
no section 11; the § 16 hypotheses list numbers 1–5 then restarts at 4. Cosmetic, but the document
is cited by section number in agent instructions, so ambiguous numbering causes real
misreferences.

### G18 — No licence decision and no LICENSE file
`PRODUCT_FOUNDATION.md` § 15 defers the open-source/commercial decision, and the dependency policy
requires checking licence compatibility "for potential commercial distribution" — a check that
cannot be performed against an undefined target. A provisional stance is enough for now; the file
is missing entirely.

### G19 — Ambient/photo-frame is over-documented relative to its scope
`MVP.md` lists photo-frame/Ambient as explicitly **not** MVP, yet it occupies large parts of
`DISPLAY_BEHAVIOR.md`, a principle (P14), roadmap items and constraint lists. The thinking is
sound and worth keeping, but it should be consolidated into one clearly-marked future section
rather than distributed across the contracts an implementer must read. Directly relevant to the
project's "productive work only" rule.

### G20 — Documentation and code language convention is unstated
All documents are English while the maintainer works in German. Now recorded in `ONBOARDING.md`
§ 6; belongs in `AGENTS.md` if it is to be binding.

### G21 — NFC details undefined
UID format and normalisation, unassigned-tag behaviour, one tag mapped to multiple actions,
re-presenting a tag during playback of its own content, and whether `NfcRemoved` stops playback.
The slice needs a simulated UID launching one item, so at least identity handling is needed now.

### G22 — No glossary
"Kids Early", "Experience Profile", "Profile", "Capability", "Scene", "Action", "Reference /
Compatible / Community" are used across documents with slightly varying meaning. `Profile` in
particular means both a user and a UI configuration depending on the document.

---

## Recommended closing order

1. ~~G02 (git)~~ — done.
2. G01 (technology ADRs) — the actual gate. Nothing else can be delegated first.
3. G03 (layout + run/test instructions) — write together with the first ADRs.
4. G04, G05 (display state machine + concrete values) — the largest correctness risk in the slice.
5. G06, G07 (input bus + event channel) — follow directly from G01.
6. G08–G14 — write each one immediately before implementing the slice step that needs it, not all
   up front.
7. G15–G22 — batch as documentation hygiene; G16, G17, G20 cost minutes.
