# Handover

**Date:** 2026-08-18
**Reason:** end of session; another assistant takes over for the rest of today.
**Supersedes:** the handover of 2026-08-17, whose contents are all done.

Read `ONBOARDING.md` first — it is the entry point and this document assumes it. This file records
only what is *in flight*: state that is not obvious from the repository itself.

## Where things stand

`main` is clean and green: **908 tests, ruff, ruff format and mypy pass.** Run the checks **bare,
never through a pipe** — a piped exit status comes from the pipe, not the command. That is M-004 in
`MISTAKES.md`.

```
ruff check . && ruff format --check . && mypy && pytest
```

`main` is **13 commits ahead of `origin/main` and nothing has been pushed.** That is deliberate; the
maintainer pushes.

| Slice step | State |
|---|---|
| 1 — domain model + state machines | done |
| 2 — persistence | done |
| 3 — audio adapter | done |
| 4 — semantic input bus + simulator | done |
| 5 — application services | done, including content ingestion |
| 6 — typed state channel | **partly** — `PlaybackSnapshot` and `DisplaySnapshot` exist; nothing merges them for a UI |
| 7 — Kids Early UI | not started. **No `ui/` directory exists.** |
| 8 — display policy | done today: ports, service, readiness ladder |
| 9 — end-to-end tests | not started |
| 10 — Reference Hardware adapter | not started |

Every documentation gap the vertical slice depends on is now closed (`docs/DOCUMENTATION_GAPS.md`).
Open and blocking nothing: G24 (packaging and display server) and the hygiene set.

## 1. What changed today, and why it matters

**A project-direction correction, and it is the most important thing in this file.** ADR 0015
established:

> **AQENO is built to be excellent, not to justify a business.**

A competitive review earlier the same day judged every capability by market differentiation and
recommended narrowing the product. The research was kept; the framing was rejected, because the
premise was wrong — there is no market to enter, there is one child who will use this device daily.

Two rules follow, and a new agent will get decisions wrong without them:

- **"Not a USP" is never a reason not to build something.** Neither is "a competitor already has
  this". The test is `AGENTS.md` § "Deciding what to build": *does this make AQENO meaningfully
  better for the person using it?*, with *better or merely bigger?* as the guard.
- **`docs/product/COMPETITIVE_REVIEW.md` is a benchmark, not a scope authority.** It is written
  persuasively and will read as binding if you do not know this.

Also today: content ingestion (ADR 0014), the readiness ladder and display service (ADR 0016), the
readiness specification (`READINESS_STATES.md`) and a fix to the display state machine.

## 2. Waiting on the maintainer: two open decisions

A display, ambient-interaction and display-modularity directive arrived at the end of the session.
**It is analysed but not yet written into the documentation, because two product questions are the
maintainer's to answer.** Do not decide them yourself.

The directive's canonical statement is *"Display is a capability, not a dependency"* — AQENO must be
a complete audio device with no display attached. The full analysis is in the final assistant message
of the previous session; its substance:

**The architecture already satisfies most of it.** `test_import_boundaries.py` forbids every layer
from importing `aqeno.ui`; there is no `ui/` package; `UI_READY` is never reached today and the
process runs correctly that way. Unplugging the display stops exactly one thing: **choosing content
that has no token assigned.**

**Question 1 — naming.** The directive's "AMBIENT" (glanceable: title, chapter, clock, entered
automatically after inactivity) is the *opposite* of the accepted `AMBIENT` state, which is the
deliberately enabled visual mode and carries the invariant *"Ambient is never an automatic fallback
for inactivity"* plus product principle P14. The glanceable state the directive describes is
structurally the existing **`DIM`** — automatic after inactivity, dimmed, no controls, `dim_hold`
onward to `OFF`. Recommendation: implement glanceable as `DIM` with defined content, keep `AMBIENT`
meaning what it means. Rejected alternative: renaming states in an accepted normative table.

**Question 2 — Kids Early.** It currently goes `INTERACTIVE → OFF` after 30 s (`allows_dim=False`,
`dim_brightness=0`). A glanceable stage means a faintly lit screen in a child's room after 30 seconds
instead of darkness. Does Kids Early get it, or is glanceable for kitchen/Easy/Standard only?

**Two further conflicts to resolve when writing this up:** § 13 of the directive (a clock shown when
idle) contradicts P14 directly; and the directive's "Ambient Idle" must stay distinct from the photo
frame, which remains a future concept.

**The agreed minimal implementation, once those are answered** — four items, one new Core file:

1. `adapters/display/none.py` — a null panel reporting `PanelCapabilities(authoritative_off=True,
   brightness_control=False, touch=False)`. With no panel, authoritative off is simply true. Zero
   changes to the service, the policy or the LEDs.
2. Display detection in the composition root only. **No hotplug.**
3. Glanceable as `DIM` plus config values and a rendering description in `DISPLAY_BEHAVIOR.md`.
4. `ports/ambient_light.py` with `read_lux()`, a VEML7700 adapter, smoothing and hysteresis as policy
   in the display service. No sensor logic in the domain.

**Do not build:** a capability DSL, a display-plugin or universal-input framework, runtime hotplug, a
burn-in engine, an adaptive-brightness engine, or product variants. All seven were ruled out
explicitly.

**Documentation plan agreed but not executed:** ADR 0017 (`Display as optional capability`),
`PRODUCT_FOUNDATION.md` for the principles and the P14 resolution, `DISPLAY_BEHAVIOR.md` for
glanceable and headless feedback, `HARDWARE_REFERENCE.md` for the VEML7700 as an RH1 candidate and
AMOLED / Waveshare 5" as RH2 candidates. No new redundant documents.

## 3. Known gaps worth acting on

- **No update or recovery path exists.** It is the only row of the failure comparison in
  `COMPETITIVE_REVIEW.md` with no answer, and it is the most realistic way a self-built device dies.
- **Setup requires maker knowledge and there is no interface**, so the primary design case — a child
  using the device daily — is still untested. `docs/product/USE_OBSERVATIONS.md` is empty and waiting
  for its first entry.
- **`CONFIGURATION_DEFAULTS.md` § 3.3 volume calibration** is still open. The current ceilings are
  placeholders, not a hearing-safety guarantee; it needs a sound-level meter and Reference hardware.
- **G24, `eglfs` versus Wayland.** ADR 0016 deliberately made this *observable* rather than deciding
  it: the real panel adapter is not finished until it reports `authoritative_off` truthfully on
  Reference Hardware 1.
- **Ingestion, two documented deviations** (`CONTENT_INGESTION.md` § 15): every scan re-probes every
  file, and MP4 chapter atoms are not read, so an `.m4b` falls back to one chapter.

## 4. Housekeeping the assistant could not do

`docs/history-rewrite-plan.md` is untracked and **obsolete** — the rewrite it describes was completed
and `main` carries the result. Deleting it was blocked by the environment's permission classifier, so
it is still on disk. The same applies to four stale branches, all behind `main`:
`wip/audio-adapter` (also on `origin`), `wip/content-ingestion`, `wip/display-service`,
`rewrite/quality-history`, `backup/pre-quality-history-rewrite`.

```
rm docs/history-rewrite-plan.md
git branch -D wip/audio-adapter wip/content-ingestion wip/display-service \
  rewrite/quality-history backup/pre-quality-history-rewrite
```

Deleting `origin/wip/audio-adapter` is a remote change and needs the maintainer's explicit go-ahead.

## 5. How this project works

- **Architecture and specification come from the assistant; implementation is delegated** to a
  subagent and then reviewed against the specification. That pattern produced today's ingestion and
  display work and is worth keeping.
- **Delegated agents must be told what not to touch.** Today's display agent was forbidden from
  editing `domain/display.py`; it found a real defect there, reported it instead of patching it, and
  the fix was made deliberately with a spec amendment. That is the outcome the rule exists for.
- **Every commit carries an honest `Co-Authored-By` trailer** — ADR 0006 § 7 makes provenance
  load-bearing because the copyright status of AI-generated code is unsettled.
- **Commit subjects are lowercase, imperative, and state the motive or the non-obvious decision.**
  Read `git log --oneline -20` before writing one.
- Documentation is English; the maintainer works in German.

## 6. Standing constraints

- **This is a personal project** built for the maintainer's son. Licensing, commercialisation and
  publication are deferred by intent (ADR 0006, on hold). Do not treat them as live.
- **Productive work only** — `AGENTS.md`. Optimal does not mean maximal, and YAGNI still binds.
- **The repository is private and must stay private** until `CONTRIBUTING.md` with a contributor
  agreement exists (ADR 0006 § 7). Publishing without it is the one step that cannot be undone.
