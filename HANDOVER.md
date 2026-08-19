# Handover

**Updated:** 2026-08-19
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
rather than guessed.

The current software slice adds configurable logical physical controls, bounded RH1 remote deployment,
the HiFiBerry MiniAmp platform path, a fail-closed Plymouth handover and — since 2026-08-18 — the
physical navigation vocabulary that makes the everyday journey operable without touch. Verification is
green: **1122 passed, 1 hardware test deselected**; canonical mypy, Ruff, Admin check/build and all
five browser E2E tests pass. The physical RH1 acceptance boundary below remains open.

The step log below stops at Step 10 / `851898c`. The management API, Admin foundation and RH1
platform integration that followed (`5c3108f` … `fc41de0`) are recorded in git history and in the
contracts they changed, not here; that gap is known rather than an indication they are missing.

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
| 10 — Reference Hardware adapters | configurable controls/LED software done; physical/display evidence externally gated |

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

### 2026-08-18 — product identity, physical-first interaction and the touch-free slice

- Audited the product, UI, platform and hardware contracts against a sharpened product definition
  and recorded three ADRs: **0023** identity, three pillars (audio, time, personal connection) and
  the attention principle; **0024** physical-first / display-assisted / touch-optional, NAV-vs-VOL
  separation, the transport rocker and RH1 as prototype input; **0025** display class preference
  without dependency, no required status LED, and the time pillar's binding constraints.
- Named the one hard conflict: the implemented Kids Early surface could only be operated by touch —
  selection and Home were `TapHandler`s — and `DEVICE_UI_BLUEPRINT.md` stated that rule deliberately.
  ADR 0024 overturns it; the blueprint, principles, `PLATFORM_CONTRACTS.md`, `MVP.md` and
  `DISPLAY_STATE_MACHINE.md` were updated rather than left to contradict it.
- Implemented the smallest testable slice: semantic `FocusPrevious`/`FocusNext`/`Select`/`Back`
  events named apart from transport, a `navigation_encoder` logical control with registry actions and
  inert defaults, display-machine **Group G** (navigation wakes like touch and the waking input is
  consumed), a wrapping focus model in `DeviceUiState`, a visible QML focus ring, and simulator keys
  `a`/`d`/`s`/`b`.
- Added `tests/scenarios/test_touch_free_operation.py`: the whole everyday journey driven without a
  single touch, with a touch probe that is proven able to fail. Verification after the change:
  1122 passed, 1 deselected; Ruff, format, mypy, Admin check/build and five E2E tests green.
- Rejected on purpose: a capability framework (ADR 0017 § 1 already refused one; ports already report
  what hardware exists), any clock/timer/alarm implementation, and removing touch from RH1.

### 2026-08-18 — control semantics decided, contracts corrected

- Back is no longer open: **LEFT = back, RIGHT = forward, NAV = focus/select, VOL = volume/play**
  (ADR 0024 § Amendment). No OK button, no long press for back, and the flat rule that everyday
  operation must not require long-press or double-press gestures. Long press survives for
  setup/service only, and no default binds one.
- LEFT/RIGHT are modelled as back/forward resolved by content context, not as previous/next track.
  Their current slice resolution stays linear playback, so RH1 defaults are unchanged. The one cell
  left undecided on purpose — what LEFT does on Now Playing during playback — is recorded in ADR
  0024 § A3 and decided with the first browsing level.
- Wake behaviour is now documented as a property of the resolved action, not the button. Volume and
  Play/Pause are explicitly excluded from Group G: a first volume step in the dark reaches audio
  instead of being spent lighting the panel.
- Code changes were deliberately small: the NAV long-press default became unassigned, and
  `display.wake` is short-press only. Tests cover both, including at the Management API boundary.
- Also recorded: `PRODUCT_FOUNDATION.md` P20 (inherent physical feedback before invented feedback),
  the RH1 control plan LEFT · NAV · RIGHT · VOL with no middle OK switch, visual timer as the first
  time capability, the Zero-2-W performance test after RH1 validation, and "consolidation before
  fragmentation" in `AGENTS.md`.
- Verification: 1124 passed, 1 deselected; Ruff, format and mypy green. No admin source changed, so
  the committed bundle is untouched.

### External verification boundary

- Install the optional `rh1` dependencies on the Raspberry Pi and verify both boards coexist on the
  assembled I²C bus at `0x36` and `0x30`, including direction, press edges and sustained polling.
- Record the exact acquired display revision. Choose/verify its display-server integration before a
  real panel adapter can truthfully report authoritative OFF, brightness or touch routing (G24).
- The RH1 semantic LED adapter now implements fixed warm `off`/`subtle`/`clear` output and Night/OFF
  override. Actual NeoPixel true-off, brightness and electrical behaviour still require RH1 evidence;
  initialization failure degrades to `NullStatusLeds` without affecting playback.
- The HiFiBerry MiniAmp and two QUARKZMAN 3 W / 4 ohm speakers are the selected RH1 audio path; the
  previous Soldered MAX98357 is no longer part of RH1 because it required soldering. MiniAmp receipt,
  wiring and physical validation remain to be recorded;
  their wiring, Linux audio path, channel behaviour, sustained output and calibration are unverified.
- NFC, VEML7700 and final power components remain unselected or explicit feasibility candidates. No
  adapter should pretend they exist.
- A conditional Plymouth theme and first-frame handover exist, but remain disabled: the repository
  has no canonical AQENO SVG and G24 still lacks the real FREENOVE DSI adapter. No placeholder brand
  asset or false successful handover is installed.
- Hardware-only boot/wake timing, full-dark output and child-safe calibrated volume remain physical
  measurements. The single deselected test is intentionally in that class.
- **RH1 cannot yet demonstrate the complete touch-free journey physically.** Since ADR 0026 the box
  can carry PREVIOUS, NEXT, HOME and VOLUME with hardware on hand, so the return path from Now
  Playing is no longer touch-only. Focus movement and activation still need a SELECT encoder and
  stay on the desktop simulator until one is chosen against the Rotary Control Contract. The
  address-jumper question on a second 5880 must be checked against the no-solder gate first.

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

### 2026-08-19 — hardware interaction and accessibility consolidated

- Consolidated the accumulated physical-interaction, accessibility, NFC, night, illumination,
  sensing and hardware-variant decisions into **ADR 0026 — AQENO Hardware Interaction Contract**,
  and gave it a normative companion, `docs/implementation/INTERACTION_MATRIX.md`, covering 36
  situations against every control. Two new documents; everything else was updated in place.
- **The control set is five, not four:** SELECT · PREVIOUS · NEXT · VOLUME · HOME, each with one
  permanent meaning. This supersedes ADR 0024 § A1, § A3 and § A4.
- Named the conflict that forced it: ADR 0024 § 2 required a control to mean the same thing in every
  state, then made LEFT/RIGHT context-resolved. Its own § A3 open cell was the symptom. A person who
  cannot see the screen cannot know the context, so they cannot know what the control will do.
- HOME closes ADR 0024 § A3 and gives every state a way out. It **wakes and acts on one press**
  rather than being consumed (new `DISPLAY_STATE_MACHINE.md` note 17): consumption protects against
  an unseen *context-dependent* action, and HOME has none.
- Recorded as principles P21–P24: blind operation, tactile identity, accessibility without looking
  accessible, and light that assists without ever defining. **DARK means zero visible light**,
  including a glowing HOME key and any unavoidable indicator — a purchasing constraint, not only a
  software one.
- Decided without implementing: device power states `ACTIVE`/`SLEEP`/`OFF` with no everyday power
  button; the night illumination vocabulary (`off` only exists); ambient-light + proximity sensing
  with the VCNL4040 as target candidate and the ordered VEML7700 as RH1's comparison baseline; the
  flat, recess-free NFC object area; optional magnetic positioning; the AQENO Rotary Control
  Contract. No proximity port, no capability framework (refused for the fourth time), no purchase.
- Code changes were kept to reconciliation: logical controls renamed to their permanent roles
  (`select_encoder`, `previous`, `next`, `volume_encoder`, `home`), the `Back` event became `Home`,
  `navigation.back` became `navigation.home`, RH1's NeoKey sockets became 0/1/3 with a deliberate
  gap at 2, and one new scenario proves HOME wakes and acts in the same press.
- **RH1 gained a control without a purchase.** HOME is a third Cherry MX switch in a free NeoKey
  socket; PREVIOUS, NEXT, VOLUME and HOME now all exist on the box. Only SELECT is still missing, so
  the physical Now-Playing-to-Home path is no longer touch-only.
- Design conflicts recorded rather than resolved: alarm snooze on the VOLUME press (C1), blind timer
  cancellation (C2), transport in `AMBIENT` (C3), radio favourites without a domain model (C4), and
  shutdown having no control at all (C5).
- Verification: 1125 passed, 1 deselected; Ruff, format, mypy, Admin check/build and the browser E2E
  tests green.

### 2026-08-19 — RH1 hardware ordered, inventory consolidated

- The BerryBase order was placed, so the last `PENDING_ORDER` items became `ORDERED`: SparkFun Qwiic
  Twist DEV-15083 as **SELECT**, 3 × Elecrow 100 mm Qwiic cables, 2 × Elecrow 22.2 mm illuminated
  knobs. **All five AQENO controls now exist as hardware for the first time.**
- Ran a hardware acceptance check against vendor documentation before that purchase. Qwiic Twist and
  VCNL4040 are both `APPROVED_FOR_RH1`; the Twist's 6 mm shaft, 24 detents, momentary press, address
  `0x3F` and PWM reaching `(0,0,0)` all check out. The earlier question about a second Adafruit
  5880's address jumper is moot — RH1 uses no second 5880.
- One assumption was corrected by that check: the Adafruit 5625 is a **five-port passive hub whose
  ports are all parallel**, so the uplink consumes one and four remain. Four devices fit exactly; the
  later sensor comparison needs one daisy-chain hop, not a second hub.
- **`SHOPPING_LIST.md` became `INVENTORY.md`, the single canonical hardware record.** The duplicate
  BOM in `HARDWARE_REFERENCE.md` is gone; that document now answers only *why* a component is used,
  what its interfaces and limits are, and which tests it owes. Every component carries two
  independent dimensions — `possession_status` and `product_role` — so "we ordered it" can never
  again be read as "we decided it".
- **VCNL4040 is accepted but deferred**: unavailable, deliberately not ordered. The VEML7700 is RH1's
  real working ambient sensor, not a placeholder, and **proximity simply does not exist** — it is not
  simulated to look present. `DARK means zero visible light` stays fully testable without it.
- Verified in code rather than assumed: the later VEML7700 → VCNL4040 swap is one adapter behind the
  existing `AmbientLight` port, and `DisplayService` already accepts `None` for an absent sensor. No
  Display, Night or UI logic changes, and no capability framework is created.
- The owned 125 kHz **EM4100 USB RFID reader is documented as `TRANSITIONAL`** — explicitly not
  AQENO's NFC solution. It lets the tag chain be built without a purchase. No adapter is written
  before the physical device is identified. `NFC_REFERENCE_CANDIDATE.md` is marked deferred.
- **RH1 procurement freeze is active: `BUY NOW = nothing`**, with one documented exception path for a
  proven missing connector. A seven-phase hardware smoke test is now the first thing to run on
  delivery (`RH1_VALIDATION_CHECKLIST.md`).
- No code changed. Verification: 1125 passed, 1 deselected; Ruff, format and mypy green.

### 2026-08-19 — the Device UI became a product surface

- Rebuilt the Device UI around **THE DISPLAY SHOWS. THE HARDWARE OPERATES.** The information
  architecture is now three surfaces — **Home → Browse → Now Playing** — with HOME returning from
  any of them in one press, so no back stack exists.
- **Home is no longer a tile grid.** One content area is dominant at a time, and areas come from the
  content kinds ADR 0009 already defines. An area exists only while the library holds accessible
  items of that kind, so an empty capability has no surface at all (P15). Browse is the one shallow
  level the blueprint always allowed; ADR 0024 § A3 required it before navigation semantics could
  settle.
- **Removed the virtual controls**: the on-screen Home button and the playing/paused status pill are
  gone. All five of those actions are physical, and drawing them invites reaching for a panel that
  may be off. Paused now reads from the progress bar going quiet plus one small mark.
- Added a small device design system (`ui/qml/Theme.qml`) and split the surfaces into their own QML
  files. Geometry scales sub-linearly from one `unit`, so the hierarchy survives a ~4" panel instead
  of becoming a shrunken 7" composition; secondary context drops out below a compact threshold.
- **One real bug surfaced and was fixed**: a Play/Pause press while browsing reset the surface to
  Home, because any playback snapshot without content forced it. A transport control was navigating
  — exactly what ADR 0026 § 3 forbids. Only Now Playing may now be left because playback ended.
- Unassigned tokens gained a calm sentence, and only while the panel is already lit. In the dark an
  unassigned token still does exactly nothing (`DISPLAY_STATE_MACHINE.md` note 7).
- `scripts/device_ui_screenshots.py` renders every state offscreen at 800 × 480 and 480 × 320. The
  screens in this change were reviewed as images, not as QML source.
- Verification: 1133 passed, 1 deselected; Ruff, format and mypy green.
- **Deliberately not built:** the Clock/Ambient, Timer, Alarm and Message screens. Their visual
  direction is recorded in ADR 0025 and ADR 0026, but none has domain behaviour, and giving an
  unavailable capability a device surface is precisely what P15 forbids. They arrive with their
  capabilities.

## Next action

1. Wait for delivery, then run the **seven-phase hardware smoke test** in
   `RH1_VALIDATION_CHECKLIST.md` before any further implementation: I²C → controls → blind operation
   → mechanics → knobs → light → tag-reader identification. Then the documented
   stereo/control/offline acceptance sequence, with measured evidence.
2. Supply the canonical AQENO SVG and resolve G24's real DSI adapter before enabling the Plymouth
   presentation and measuring splash-to-first-frame handover.
3. Fit three Cherry MX switches as PREVIOUS, NEXT and HOME on NeoKey sockets 0, 1 and 3, leaving
   socket 2 empty, and verify the layout and blind findability. Write the Qwiic Twist input adapter
   only once the board is physically present and Phase 1 passes.
4. Open UX questions that only real use can answer: whether HOME removes the need for a BACK control
   once browsing is deeper than one level (ADR 0026 § 4), what counts as a "section" per content
   kind, whether focus wrapping reads as helpful or confusing to a three-year-old, and the design
   conflicts C1–C5 in `INTERACTION_MATRIX.md` § 9.
5. Documentation consolidation, when there is a natural occasion: `docs/DOCUMENTATION_GAPS.md` is
   now mostly historical — 11 of 24 gaps are marked closed, 2 deferred by intent, and several open
   ones (G08 failure taxonomy, G16 roadmap contradiction, G20 language convention) were overtaken by
   documents that now exist. The proposal is to move the genuinely live items to their owning
   documents — G24 to `HANDOVER.md`/`ROADMAP.md`, G21 to `NFC_REFERENCE_CANDIDATE.md`, G15 to
   `DEVICE_UI_PRINCIPLES.md`, G10 to `FAILURE_STATES.md` — and reduce the file to a short historical
   note. G17 (duplicate `## 12.` in `PRODUCT_FOUNDATION.md`) needs one deliberate renumbering pass
   because other documents cite those section numbers; it should not be half-fixed in passing.

## Standing reminders

- Run quality commands directly, never through a pipe (`MISTAKES.md` M-004).
- Preserve unrelated user changes and keep commits conceptually narrow.
- Every AI-authored commit needs an honest `Co-Authored-By` trailer (ADR 0006 § 7).
- Push only on the maintainer's explicit instruction.
- Remaining hardware-only questions include true panel OFF/display-server behaviour, wake/startup
  timing and calibrated child volume. Do not fabricate results without Reference Hardware.
