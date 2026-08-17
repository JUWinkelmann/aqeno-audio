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

**Status 2026-08-17 — the blocking set is clear.** All seven blocking gaps are closed or deferred by
intent, and three of the seven important gaps are closed.

- **Closed:** G01 (ADRs 0001–0003, 0005, 0007–0009 accepted), G02, G03, G04, G05, G06, G07, G09,
  G11.
- **Deferred by intent:** G18, G23 — personal project, nothing published.
- **Open and blocking nothing yet:** G08, G12, G13, G14, G24, and the hygiene set.
- **The one open item with a deadline quality:** the volume calibration in
  `CONFIGURATION_DEFAULTS.md` § 3.3, which needs a sound-level meter and Reference hardware.

Implementation of `FIRST_VERTICAL_SLICE.md` is no longer blocked. G06 (input bus and simulator) was
closed by ADR 0011; `DEVELOPMENT.md` contains the keyboard mapping and the ADR fixes delivery
semantics. Slice step 4 implements that contract.

---

## Blocking — the vertical slice cannot start until these are closed

### G01 — No technology decisions exist — **PARTIALLY ADDRESSED 2026-08-17, awaiting acceptance**
`ARCHITECTURE.md` § "Decision still open" lists SBC, frontend framework, playback engine, local
database, remote architecture, packaging and licence as unlocked. `AGENTS.md` requires an ADR before
any of them is fixed.

Status of the decisions needed before code:

| # | Decision | Status |
|---:|---|---|
| 1 | Implementation language and runtime | ADR 0001 — **Proposed** |
| 2 | UI stack | ADR 0002 — **Proposed** |
| 3 | Audio playback engine | ADR 0003 — **Proposed** |
| 4 | Dependency licensing constraints | ADR 0004 — **Proposed** |
| 5 | Internationalisation (DE/EN) | ADR 0005 — **Proposed** |
| 6 | Local persistence mechanism and atomicity | **missing** — see G09 |
| 7 | Local API / event channel | **resolved by ADR 0002** (in-process) — see G07 |
| 8 | Test framework and how ports are faked | **missing** — see G11 |

ADRs 0001–0005 are Proposed, not Accepted. Until they are accepted, `ARCHITECTURE.md` § "Decision
still open" stays as-is and no implementation may rely on them. Gap G01 closes when they are
accepted and items 6 and 8 exist.

### G02 — Not a version-controlled repository — **CLOSED 2026-08-17**
The directory was not a git repository. Now initialised on `main` with remote
`git@github.com:JUWinkelmann/aqeno-audio.git`. The nine original documents are committed as a
single baseline; their pre-repository history is gone. See `MISTAKES.md` M-001.

### G03 — Repository layout, build and run instructions — **CLOSED 2026-08-17**
`DEVELOPMENT.md` supplies the toolchain, the layout mirroring `ARCHITECTURE.md`'s layers, six rules
the layout enforces, run targets including the fake-hardware desktop loop and its keyboard mapping,
and the test commands. Original gap text follows.


No directory structure for the layers in `ARCHITECTURE.md`, no module naming, no dependency
manifest, no "how do I start it", no "how do I run the tests". `CLI_START.md` asks the agent to
produce a file/module plan — meaning the layout is currently expected to be improvised per
session, which guarantees drift.

### G04 — Display state machine — **CLOSED 2026-08-17**
Specified as a normative transition table in `docs/implementation/DISPLAY_STATE_MACHINE.md`: five
states, six event groups, seven named guards, every cell defined, plus wake target, brightness per
state and ten testable invariants. It also answers two of `DISPLAY_BEHAVIOR.md`'s open questions
(wake target is Now Playing during playback; NFC does not wake the display) and flags them for user
testing. Original gap text follows.


`DISPLAY_BEHAVIOR.md` lists five states and a set of prose rules. There is no transition table.
Undefined today:
- which events cause which transition, and which events are explicitly ignored;
- what happens on `WakeRequest` while `AMBIENT`, or while Night policy is active;
- whether `DIM` is reachable at all in Kids Early;
- what `SETUP` may interrupt, and how it is exited;
- precedence when Night policy, Ambient schedule and an explicit wake conflict.

This is the highest-value gap to close: the slice's items 7–9 and its dark-room definition of done
are all this state machine, and prose rules will be interpreted differently by every implementer.

### G05 — Concrete configuration values — **CLOSED 2026-08-17, with one open calibration task**
Specified in `docs/implementation/CONFIGURATION_DEFAULTS.md`: display timeouts per profile,
brightness, volume ceilings, resume persistence, sleep timer and NFC debounce, each with a default, a
range and an editability tier.

**One item remains genuinely open and is not a documentation gap:** the volume ceilings are
conservative placeholders in a logical 0–100 scale, which is not a hearing-safety guarantee because it
is a percentage of unknown amplifier and speaker hardware. § 3.3 contains a calibration procedure to
measure actual dB(A) on Reference hardware and replace the placeholders. That is a P2 hardware task,
and it is the one thing in this document that should not stay undone. Original gap text follows.


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

### G06 — Semantic input bus and simulator — **CLOSED 2026-08-17 (by ADR 0011)**
Slice step 4. `PLATFORM_CONTRACTS.md` defines the seven event types but not the bus: delivery
semantics, ordering, whether `VolumeDelta` coalesces, whether events are queued while `BOOTING`.
ADR 0011 defines synchronous, registration-order delivery without replay or coalescing.
`DEVELOPMENT.md` defines the desktop keyboard mapping; the simulator implements the same `InputBus`
port as hardware controls.

### G07 — Local API / event channel — **CLOSED 2026-08-17 (by ADR 0002)**
Slice step 6 was "local API/event channel" with zero further description. ADR 0002 decides that the
UI runs **in-process** with the application core, communicating via Qt signals and an
application-level event bus. There is therefore no local API, no serialisation format and no network
listener — which also removes the unauthenticated-management-interface risk that `AGENTS.md` warns
about. Slice step 6 should be restated as "application event bus" rather than "local API".

---

## Important — needed before the slice's definition of done can honestly be met

### G08 — No failure taxonomy or calm-state specification
`USER_JOURNEY_KIDS_EARLY.md` § 8 requires "a calm, recoverable state" with no technical language.
Not implementable as written. Needed: enumerated failure cases (file missing, unreadable audio,
stream unreachable, unassigned NFC tag, empty library, storage full, no audio device), and for
each — child-facing representation, whether audio continues, whether the display may wake, and
what is logged. This is also the boundary where a weaker implementer will leak stack traces into
the UI.

### G09 — Persistence — **CLOSED 2026-08-17 (by ADR 0007)**
SQLite in WAL mode with `synchronous=NORMAL` for domain data, a hand-editable TOML file for settings,
atomic replace with `fsync`, XDG locations with environment overrides for tests, forward-only
migrations with a pre-migration copy, and defined degraded behaviour for a read-only filesystem or a
corrupt database. Original gap text follows.


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

### G11 — Test strategy — **CLOSED 2026-08-17 (by ADR 0008)**
pytest with four layers, port contract suites run against both fakes and real adapters, an injected
`Clock` with no `time.sleep()` permitted, a table-driven state-machine suite, the import-boundary
test, generated audio fixtures, and a mapping from every `AGENTS.md` invariant to a named test — plus
two safety tests this project needs beyond that list. Original gap text follows.


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

### G18 — No licence decision and no LICENSE file — **DEFERRED BY INTENT 2026-08-17**
AQENO is a personal project for the maintainer's son; nothing is published or distributed, so no
licence is needed yet. A `LICENSE` file and the licence choice become necessary **before** the
repository is made public, not before implementation. The analysis below is retained for that moment.


ADR 0004 supplies the missing constraint: the project licence stays deferred, but all work proceeds
under a binding interim rule (keep the proprietary-commercial path open; no GPL code linked into the
application). The dependency policy in `AGENTS.md` is now mechanically checkable.

Still open: AQENO's own licence, and there is still no `LICENSE` file. ADR 0004 § Consequences
records that keeping the commercial path open has a concrete price in the MVP, so the choice should
be made deliberately — see also the commercialisation question, which is what actually decides it.

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

### G23 — No commercialisation or regulatory model — **DEFERRED BY INTENT 2026-08-17**
Not a gap: there is no commercialisation because AQENO is built for the maintainer's son. Nothing is
placed on the market, so hardware compliance, toy-safety positioning and GDPR do not arise. The
analysis below is retained in case that ever changes. **Volume limiting survives as a genuine
hearing-protection requirement** — see G05.


Added and resolved 2026-08-17. The maintainer's governing requirement is no liability, which
determines the answer: AQENO is a **non-commercial** open-source project under GPL-3.0-or-later, with
no revenue from any source. ADR 0006 records this, together with the positioning rules that protect
it — not marketed as a toy, no safety claims, build-at-your-own-risk notices.

Consequences for this document:
- EU hardware compliance (CE, EMC, RoHS, WEEE/ElektroG, GPSR) does not arise: nothing is placed on
  the market.
- Toy Safety Directive 2009/48/EC and EN 71 are avoided by positioning, which is now a binding
  documentation rule rather than a marketing preference.
- **GDPR falls out of scope entirely** — without a hosted service AQENO is not a controller, so no
  DPIA, no Art. 8 child-consent handling, no processing agreements.
- Residual liability is *not* zero. ADR 0006 § Consequences lists what survives: intent, gross
  negligence, instruction liability for published build guides, and licence compliance.

The one item that remains open is `LICENSE` itself — see G18.

### G24 — No packaging, deployment or display-server decision
Added 2026-08-17. ADR 0002 and ADR 0004 both depend on decisions that do not yet exist: whether the
app runs under `eglfs` or a Wayland compositor, whether Qt comes from distribution packages or a
pinned build, how updates are delivered, and how LGPL replaceability is guaranteed on a shipped
device. The display-server choice in particular determines whether authoritative panel `OFF` works
at all, so it must be spiked early despite being nominally a packaging concern.

---

## Recommended closing order

1. ~~G02 (git)~~ — done.
2. ~~G07 (event channel)~~ — done via ADR 0002.
3. ~~G18, G23 (licence, commercialisation)~~ — deferred by intent; personal project, nothing
   published. Revisit only if publication becomes real.
4. ~~G04, G05 (display state machine + concrete values)~~ — done. Volume calibration (§ 3.3) remains
   as a hardware task.
5. ~~G01, G03, G09, G11~~ — done. ADRs 0001–0003, 0005, 0007–0009 accepted; `DEVELOPMENT.md` written.
6. **Implement `FIRST_VERTICAL_SLICE.md`** in its documented order. This is now the top item.
7. G08, G12, G13, G14 — write each immediately before implementing the slice step that needs it, not
   all up front. G14 grew with ADR 0009: ingestion must detect content kind, group multi-file works
   and extract chapters.
8. G24 (packaging and display server) — spike early, decide later; `eglfs` vs Wayland gates the
   display-power story, so it must be tried before the display adapter is considered finished.
9. G15–G17, G19–G22 — batch as documentation hygiene; G16, G17, G20 cost minutes.
