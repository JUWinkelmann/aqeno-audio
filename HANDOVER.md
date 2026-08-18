# Handover

**Updated:** 2026-08-18
**Purpose:** live continuation log; read `ONBOARDING.md` first.

## Operating directive

Continue the remaining scoped work autonomously. Record every started, reviewed, completed or
blocked step here so another agent can take over immediately. Delegate bounded implementation work
to a weaker model when quality will not suffer; architecture, product decisions, review and final
acceptance remain with the primary architect.

Do not broaden the First Vertical Slice. Follow `AGENTS.md`, accepted ADRs and the required
implementation specifications. Documentation is English; the maintainer communicates in German.

## Live state

Steps 7 and 9 are complete. Step 10 has the desktop-tested RH1 controls implementation in `851898c`.
Remaining Step 10 work requires physical RH1 evidence or unselected hardware and is recorded below
rather than guessed. The worktree is clean except for this handover checkpoint.

Quality result after review: **946 passed, 1 deselected**; `ruff check`, `ruff format --check` and
`mypy` pass.

| Slice step | State |
|---|---|
| 1 — domain model + state machines | done |
| 2 — persistence | done |
| 3 — audio adapter | done |
| 4 — semantic input bus + simulator | done |
| 5 — application services + ingestion | done |
| 6 — typed Device UI state channel | done (`1fcedfd`) |
| 7 — Kids Early Device UI | done (`6e295a0`) |
| 8 — display policy | done (`f88365f`, `cc493c7`) |
| 9 — end-to-end tests | done (`707de90`) |
| 10 — Reference Hardware adapters | controls done (`851898c`); physical/display work externally gated |

## Step log

### 2026-08-18 — autonomous continuation established

- Read the repository contract and created an explicit continuation goal.
- Recorded the user's autonomous-work and delegation directive in `HANDOVER.md`.
- Committed that checkpoint as `e150055 keep the live handover aligned with autonomous work`.

### 2026-08-18 — Step 7 implementation delegated

- Delegated the bounded PySide6/QML implementation to a weaker Codex model.
- Scope: one Kids Early presentation over `DeviceUiState`; Home image tiles, Now Playing,
  deliberately reduced DIM, Qt-thread marshalling, UI readiness and a Qt-free headless path.
- Explicit exclusions: administration, settings, keyboard, new frameworks, new dependencies,
  hardware adapters and product-policy changes.

### 2026-08-18 — Step 7 primary review

- Reviewed every generated file and the composition-root integration.
- Confirmed the UI imports application/domain state only; Qt remains behind a lazy composition-root
  import, so headless startup does not import or construct Qt.
- Confirmed Home is image-first, Now Playing is separate, DIM has no controls/navigation, and OFF
  removes the QML surface from hit testing.
- Found and removed an automatic `WAKE_REQUEST` emitted by UI startup. It contradicted the accepted
  invariant that nothing leaves OFF automatically. `UI_READY` now only marks readiness; an explicit
  human wake remains required.
- Added a deterministic runtime test proving UI startup advances `UI_READY` without needing or
  touching a display service. Existing model tests cover Qt-thread marshalling and OFF input gating.
- Updated `DEVELOPMENT.md` and `README.md` only where their statements that no Device UI existed had
  become false. Documented the explicit `audio,input` headless run and Qt-free `--check` path.
- Full suite result after the final lint correction: 946 passed, 1 deselected; ruff, format and mypy
  pass.
- Committed the accepted implementation as `6e295a0 give Kids Early one calm device surface` with
  honest AI co-authorship.

### 2026-08-18 — Step 9 started

- Read the canonical ten user-visible behaviours and Definition of Done in
  `docs/implementation/FIRST_VERTICAL_SLICE.md`.
- Next action is an evidence audit against existing unit, contract and scenario coverage. Only
  genuinely missing cross-boundary scenarios should be added; existing tests must not be duplicated.
- Delegated that bounded audit and implementation to the weaker Codex model
  `/root/vertical_slice_e2e`. The primary architect is independently checking the existing dark-room,
  persistence, NFC, startup and failure coverage and will review all returned changes.
- The audit found four missing cross-boundary proofs and added one focused scenario file: three local
  tiles plus UI selection and simulated NFC launch; durable resume across SQLite/session restart;
  explicit wake without audio interruption; and panel failure without loss of playback controls.
- Existing dark-room, unit and contract tests already cover DIM-to-OFF, controls while OFF, simulator
  mappings, transition completeness, readiness and import boundaries; those were not duplicated.
- Primary review accepted the scope and added explicit shutdown of the restarted PlaybackSession so
  the scenario does not leave an owned timer/service alive when its library closes.
- Full verification passed: 950 tests, 1 hardware test deselected; ruff, format and mypy green.
- Committed as `707de90 prove the vertical slice across application boundaries` with honest AI
  co-authorship.

### 2026-08-18 — Step 10 started

- Began checking the documented RH1 components against the existing ports, installed driver surface
  and hardware-only facts. The goal is the smallest concrete adapter set that can be tested honestly;
  true panel OFF, bus coexistence and timing remain hardware measurements, not desktop assumptions.
- Official Adafruit documentation verifies enough for the acquired controls only: PID 5880 uses
  seesaw at default `0x36`, button pin 24 with pull-up and inverted position for clockwise-positive;
  NeoKey 1x4 uses default `0x30` and exposes four key states. The libraries are MIT-licensed but are
  not installed on this desktop.
- Delegated a thin, lazy-imported RH1 input adapter with injected deterministic tests to the weaker
  Codex model `/root/rh1_controls`. Scope excludes display, LEDs, NFC, hotplug and generic hardware
  frameworks. NeoKey 0/2 map to Previous/Next; reserve keys remain unused.
- Display power/brightness cannot be implemented honestly until the exact display revision and
  display-server path are known and tested. LED colour/meaning is likewise not invented merely to
  illuminate acquired pixels; true dark remains preferable.
- The delegated implementation added a lazy-driver `I2cSeesawInputBus`, deterministic edge/delta
  tests, an explicit null LED adapter, RH1 optional dependencies and composition-root start/close.
- Primary review corrected two contract violations before acceptance: it replaced an unverified
  `digitalio.Pull` path with Adafruit's documented seesaw `INPUT_PULLUP` setup, and restored ADR
  0011's synchronous fail-fast listener behaviour instead of swallowing listener exceptions.
- ADR 0010 now records the optional MIT driver dependencies and removes its stale suggestion that
  the first hardware adapter should trigger a capability framework; ADR 0017 and the current human
  decision explicitly reject that generalisation.
- Final desktop result: 959 tests passed, 1 hardware test deselected; ruff, format and mypy passed.
- Committed as `851898c connect RH1 controls without coupling the core` with honest AI co-authorship.

### External verification boundary

- Install the optional `rh1` dependencies on the Raspberry Pi and verify both boards coexist on the
  assembled I²C bus at `0x36` and `0x30`, including direction, press edges and sustained polling.
- Record the exact acquired display revision. Choose/verify its display-server integration before a
  real panel adapter can truthfully report authoritative OFF, brightness or touch routing (G24).
- Status LED output needs observed true-off behaviour and a deliberately chosen semantic indication;
  AQENO currently uses `NullStatusLeds` on real composition rather than illuminating pixels without
  a product reason.
- NFC, VEML7700, final audio path and power components are not selected/acquired or remain explicit
  feasibility candidates. No adapter should pretend they exist.
- Hardware-only boot/wake timing, full-dark output and child-safe calibrated volume remain physical
  measurements. The single deselected test is intentionally in that class.

## Accepted display and hardware decisions already in the repository

- `INTERACTIVE → DIM → OFF` during playback; DIM is the glanceable presentation, not a new state.
- Idle retains existing OFF policy. AMBIENT stays explicit and never becomes inactivity fallback.
- Night/Bedtime remains authoritative and reliably dark.
- Display is optional through a null panel and composition-root selection; playback remains complete
  headlessly. No capability framework or runtime hotplug.
- Ambient light is a Lux port with VEML7700 adapter and minimal calm policy; no generic adaptive
  brightness engine.
- Repairability and standard-component principles are canonical in `PRODUCT_FOUNDATION.md` and
  `docs/hardware/HARDWARE_REFERENCE.md` (`0aede03`). No CAD, enclosure design or RH change was made.

## Next action

1. On the assembled RH1, perform the verification above and record evidence before extending Step 10.
2. Until then, the next productive software task requires a new scoped instruction or new hardware
   evidence; do not invent the missing adapter behaviour.

## Standing reminders

- Run quality commands directly, never through a pipe (`MISTAKES.md` M-004).
- Preserve unrelated user changes and keep commits conceptually narrow.
- Every AI-authored commit needs an honest `Co-Authored-By` trailer (ADR 0006 § 7).
- Do not push; the maintainer owns publication.
- Remaining hardware-only questions include true panel OFF/display-server behaviour, wake/startup
  timing and calibrated child volume. Do not fabricate results without Reference Hardware.
