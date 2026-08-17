# ADR 0008 — Test strategy

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17
**Closes:** gap G11

## Context

`AGENTS.md` § Testing expectations lists eight invariants to protect but maps none of them to a test
layer. `FIRST_VERTICAL_SLICE.md` names "offline smoke test passes" and "dark-room test passes" as
definition-of-done items with no defined mechanism. Nothing says how hardware ports are faked, where
test audio comes from, or whether CI exists.

Two properties of this project make the strategy specific rather than generic:

- **Most of the interesting behaviour is time-dependent.** Display timeouts, resume intervals, sleep
  timers and NFC debounce are all durations. Tests that sleep are slow, flaky and useless in CI.
- **Implementation is intended to be delegated to weaker models.** Tests are the specification that
  makes that safe. A delegated task with a failing test to satisfy succeeds far more often than one
  with a paragraph of prose.

## Decision

### 1. Tooling

**pytest**, plus **ruff** for lint and format and **mypy** for type checking `domain/`, `application/`
and `ports/`. Nothing else. No coverage gate, no property-based testing framework, no BDD layer —
`AGENTS.md` asks for boring technology and no bells and whistles.

### 2. Layers

| Layer | Location | What it covers | Speed |
|---|---|---|---|
| Unit | `tests/unit/` | Domain and application logic, pure, no I/O | milliseconds |
| Contract | `tests/contracts/` | One suite per port, run against **both** the fake and the real adapter | fast / slow |
| Scenario | `tests/scenarios/` | End-to-end behaviour through fakes, mapped to the invariants | seconds |
| Hardware | `tests/hardware/` | Real I2C, real display, real audio device | manual |

Hardware tests are marked `@pytest.mark.hardware` and **deselected by default**. They are run
deliberately on the Pi, never in CI.

### 3. Contract tests are the load-bearing idea

Each port defined in `PLATFORM_CONTRACTS.md` gets **one test suite that runs against every
implementation of it** — the fake and the real adapter both. This is what stops fakes from drifting
away from reality, which is the standard way a hexagonal architecture rots: the tests pass against a
fake that no longer behaves like the hardware.

Ports covered: audio, display, LED, input, NFC, persistence, network state.

### 4. Time is injected, never real

A `Clock` port is a first-class dependency. Application code never calls `time.monotonic()`,
`time.sleep()`, `datetime.now()` or a Qt timer directly.

**No test may call `time.sleep()`.** A `FakeClock` advances explicitly, so a 30-second inactivity
timeout is tested in microseconds and deterministically. This is non-negotiable: it is the difference
between a timeout test suite that runs in a second and one nobody runs.

### 5. The state machine is table-driven

`DISPLAY_STATE_MACHINE.md` is a table, so the test is a table. Every cell — event × state × guard set
— is a parametrised case, and a missing cell is a test failure rather than an oversight. Its ten
invariants each get a named test.

This is the single highest-value test suite in the project and the best candidate for delegation: the
specification is already machine-shaped.

### 6. The import boundary is a test

ADR 0001 forbids framework and hardware imports in `domain/`, `application/` and `ports/`. A test
walks the AST of every module in those packages and fails on any import outside the standard library
and AQENO's own allowed packages.

It exists because Python makes the violation a one-line accident, and because it protects the
portability the whole architecture is for. It runs in CI on every push.

### 7. Test audio is generated, never committed

No audio file is committed to the repository. Fixtures are generated at test time — silence, sine
tones, a known-length file, a deliberately truncated file, a file with no read permission. This keeps
the repository small, keeps fixtures deterministic, and avoids the licensing question that committed
sample audio would raise.

### 8. Fakes provided

`FakeClock`, `FakeAudioAdapter` (scriptable state and error callbacks), `FakeDisplayAdapter`
(records every state transition and brightness change), `FakeLedAdapter`, `FakeInputBus` (emits
semantic events), `FakeNfcReader`, and persistence against a temporary directory with
`AQENO_*_DIR` pointed at it (ADR 0007 § 4).

`FakeDisplayAdapter` recording *every* transition is what makes "the display never woke" an assertable
statement rather than a hope.

### 9. Invariant mapping

`AGENTS.md`'s eight invariants, each with the test that owns it. This table is the answer to "are we
actually testing what we said we would":

| Invariant | Test |
|---|---|
| Local content plays without internet/cloud | `scenarios/test_offline.py` — network fake reports down for the whole run |
| Playback continues when visual output sleeps | `scenarios/test_display_sleep_during_playback.py` |
| Physical volume/playback commands work with display off | `scenarios/test_dark_room.py` |
| Content resume is independent of launch method | `scenarios/test_resume_launch_paths.py` — touch, NFC and queue reach the same position |
| Unsupported hardware fails clearly | `contracts/` per port + `scenarios/test_missing_audio_device.py` |
| Role/Guardian boundaries cannot be bypassed | `unit/test_authorisation.py` |
| Display stays off through routine playback transitions | `unit/test_display_state_machine.py::test_group_d_events_produce_no_transition` |
| Startup/wake timing measurable, regressions surfaced | `hardware/test_boot_timing.py` — measured on Reference, not asserted in CI |

Two additions this project needs beyond that list:

| Invariant | Test |
|---|---|
| Power loss does not corrupt the library (ADR 0007) | `scenarios/test_power_loss.py` — kill mid-write, assert library opens and resume within 12 s |
| Child volume ceilings cannot be exceeded by any path (ADR 0006 § 6) | `unit/test_volume_ceilings.py` — encoder, touch, NFC Action, scene, and a hand-edited settings file |

The second is a safety test. It is not optional and it does not get skipped to make a build green.

### 10. CI

One GitHub Actions workflow on push: ruff, mypy, then unit, contract-against-fakes and scenario tests.
Hardware tests excluded. No matrix, no coverage upload, no badges.

## Alternatives considered

**unittest from the standard library.** No dependency at all. Rejected because parametrised cases are
central here — the state machine table and the invariant matrix both are — and pytest's
parametrisation is markedly better. One dev dependency is proportionate.

**A coverage percentage gate.** Rejected. It measures lines executed, not invariants protected, and it
reliably produces tests written to raise a number. The § 9 mapping is the real gate.

**Hypothesis for property-based testing.** Genuinely attractive for the state machine, which has clean
properties ("no automatic transition leaves OFF"). Rejected for now as an unnecessary dependency while
the table is small enough to enumerate exhaustively. Revisit if the state machine grows.

**Testing against real hardware in CI.** Rejected: no runner has an I2C bus, and a test suite that can
only run on the Pi will stop being run.

## Consequences

**Easier.** Delegated implementation becomes safe: a task can be handed over as "make these tests
pass" instead of a paragraph of prose. Timeout behaviour is testable in microseconds. Fakes cannot
drift from adapters, because the same suite runs against both.

**Harder.** Every port needs a fake *and* a contract suite before its adapter is useful, which is real
work up front. Injecting a `Clock` everywhere is mildly tedious and will be forgotten; the
no-`time.sleep()` rule is what catches it.

**Constrained.** No `time.sleep()` in tests. No committed audio. No skipping the volume-ceiling test.
Application code may not read the wall clock directly.
