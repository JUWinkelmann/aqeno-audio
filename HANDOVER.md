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

**Verification, 2026-08-19:** `1141 passed, 1 hardware test deselected`; Ruff, format, canonical
mypy, Admin check/build and all five browser E2E tests green. Nothing is pushed beyond `main`.

The First Vertical Slice is implemented and desktop-tested. Since then the interaction contract, the
hardware inventory, the Device UI and the audio/attention contracts were consolidated:

| Area | State |
|---|---|
| First Vertical Slice, steps 1–9 | done |
| Step 10 — RH1 adapters | controls/LED software done; physical evidence gated on delivery |
| Interaction contract | **ADR 0026** — five permanent controls, SELECT · PREVIOUS · NEXT · VOLUME · HOME |
| Audio, attention, Send to AQENO | **ADR 0027** — four sound classes, night ≠ mute, cloud is courier |
| Hardware inventory | `INVENTORY.md` is canonical; **procurement freeze active, BUY NOW = nothing** |
| Device UI | Home → Browse → Now Playing implemented, physical-first, presentation levels |
| Design targets | clock, timer, alarm, message, context actions drawn in `scripts/ui_preview/`, **not routed** |
| Media preparation | **ADR 0028/0029** — candidate revisions, atomic publication, Magic Budget; implementation in progress |
| Adversarial verification | role defined in `docs/agents/ADVERSARIAL_VERIFIER.md`, **not executed**; run at the next stable checkpoint |

**What is real and what is only drawn.** The device plays local content, browses it by content area,
and is fully operable with the five controls. Clock, timer, alarm and messages have **no domain
behaviour at all** — their screens exist only as design targets outside `src/`, and routing one into
`Main.qml` before its capability exists would violate P15. Proximity does not exist either; the
VCNL4040 is accepted but deliberately unordered, and the VEML7700 is RH1's working ambient sensor.

**The single blocking dependency is hardware delivery.** The Qwiic Twist, three Qwiic cables and two
Elecrow knobs are ordered; everything else in the control set is on hand. Nothing further is bought
until the parts arrive and the smoke test has run.

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
- **Design targets added afterwards, on request:** `scripts/ui_preview/` now holds seven drawn
  screens — clock, timer setup/running/finished, ringing alarm, message available and message
  playing — rendered by `scripts/device_ui_preview.py` at both viewports. They are outside `src/`,
  hold no application state and are unreachable from `Main.qml`, so an unavailable capability still
  has no device surface (P15). The visual timer follows ADR 0025 § 3: a shrinking coloured ring is
  the primary carrier and the numerals are secondary, so it reads without being able to read a
  clock. Neither the alarm nor the running timer draws a control label — C1 and C2 stay open, and a
  drawn label would settle them quietly.

### 2026-08-19 — audio, attention and Send to AQENO became contracts

- AQENO had display and illumination policies but no audio policy — while already having audio
  *rules*, scattered as per-feature clauses in `FAILURE_STATES.md` and `CONFIGURATION_DEFAULTS.md`.
  **ADR 0027** makes them one decision: four semantic classes (`FEEDBACK`, `NOTIFICATION`,
  `ATTENTION`, `ALARM`), and the class decides audibility, not the feature.
- **Found and corrected a latent defect.** `FAILURE_STATES.md` stated that Night suppresses system
  sounds, as a blanket rule. Applied to a timer or alarm — both already decided capabilities — that
  would have silenced the wake-up. Night silences `FEEDBACK` and `NOTIFICATION`; `ATTENTION` and
  `ALARM` stay audible. **Dark is not mute; Night is not a master mute.**
- Volume is no longer conceptually one number: `MEDIA_VOLUME` is what the physical control operates,
  `FEEDBACK_LEVEL` is bounded so a confirmation tone cannot inherit media loudness, and
  `ALARM_VOLUME` is separate so a quiet bedtime story cannot make the morning alarm inaudible.
- **Send to AQENO is now normative.** Recording happens in an authorised client — the device needs no
  microphone. The cloud is the courier, not the archive: the personal payload is deleted only after a
  complete download, verified integrity, atomic local persistence **and** an acknowledgement, never
  on "download started" or "transfer completed". A delivered message is local content, plays offline
  and may be heard again. Only authorised senders may send. Arrival never plays automatically and is
  completely silent at night.
- Sound assets are replaceable presentation, referenced by semantic role and never by file name, so a
  missing final asset cannot block the message domain, the attention policy or the Device UI.
  Existing and generated sounds are both allowed when rights, quality and provenance hold; NC is
  excluded; no product's sound identity is imitated; and nothing ships without a provenance record.
- **No code changed.** There is no audio-feedback implementation, no message domain and no transport,
  and none was created speculatively. Verification: 1133 passed, 1 deselected; Ruff, format and mypy
  green.
- Noted rather than fixed: the repository has **no `PRIVACY.md`**. The privacy rules this touches
  live in `AGENTS.md` § Security and privacy and `PRODUCT_FOUNDATION.md` § 15, and ADR 0027 adds the
  personal-audio rules there rather than opening a third place.

### 2026-08-19 — presentation levels, context-action pattern and a pre-reader pass

- Consolidated the remaining semantic layer of the Device UI without redoing the reduction pass.
  **Presentation levels** — `VISUAL`, `VISUAL_LABEL`, `INFORMATIVE` — are now a contract: density
  only, never a second interaction architecture, and explicitly not an age classification. The
  experience configurations of `PRODUCT_FOUNDATION.md` § 4 map onto that one axis; no profile
  defaults to `VISUAL`, which stays a preference rather than an inference about anyone.
- Visible effect on the product surface, and it is a further reduction rather than a redesign: at
  Kids Early's `VISUAL_LABEL` Home no longer prints "3 verfügbar", Browse drops "1 / 3" and Now
  Playing drops the elapsed time. One obvious thing, and a three-year-old could read none of it.
- **Pre-reader review of every screen.** Two came back text-dependent and were corrected. Timer
  Finished had its state in the word "Fertig"; it now changes silhouette — a running timer is a ring
  with an empty middle, a finished one is a solid disc — with the label demoted to confirmation and
  no borrowed checkmark. Message Available put the person in a name; where portrait material exists
  the person is now the dominant mark and the heart a small qualifier, with the text fallback kept
  and no obligation created on domain or transport.
- **Alarm Ringing gained a silhouette nothing else wears** — a full-screen frame — so it is
  distinguishable from Clock, Timer and Message at two metres without a control label and without
  aggressive animation. Audio still carries the time-critical attention (ADR 0027 § 5).
- **Pause reads at distance now.** The corner chip was too quiet, which matters most for someone who
  cannot simply hear that the audio stopped. The cover recedes and one large mark sits over it —
  state, not a control, and nothing pressable returned.
- **Context actions are a defined pattern but deliberately not a product surface.** A visual action
  carousel, two to four actions, SELECT rotating and pressing. AQENO has **no set of decided device
  context actions**: favourites exist in the domain (ADR 0019) but device-side favouriting was never
  decided, and the sleep timer exists only as settings. Inventing actions to fill a carousel is what
  the brief forbids, so it exists as a design target whose placeholders mean nothing and which can
  be judged for geometry only.
- Recorded that accent is one voice rather than a status palette: it marks the live thing, never
  carries meaning alone, and a state that needs distinguishing gets a different silhouette rather
  than a second colour.
- Verification: 1141 passed, 1 deselected; Ruff, format and mypy green. New tests hold the two rules
  that erode quietly — a level may not change what a person can do, and a drawn screen may not
  become an available capability.

### 2026-08-19 — media preparation decided, and an adversarial verifier role created

- **ADR 0028** put a publication boundary into the architecture: preparation writes a candidate
  revision no device surface can read, publication is one SQLite transaction moving a pointer, and
  startup opens a prepared revision instead of walking the media tree. `4aaf0d4`, with `76bb6f4`
  naming Pillow as the optional, lazily imported image library for artwork derivation.
- **`f102fa1` corrected an over-claim in ADR 0028 § 6.** "The completion boundary for a copy is the
  human" was written as a property of the model; it is a property of the one import path that exists.
  Atomicity comes from the candidate being unreadable until publication, not from who signals
  completion — so a later automatic import path may define its own explicit boundary without breaking
  the ADR, and the size/mtime stability check may never be promoted into that role.
- **ADR 0029** decided what prepared metadata may claim. Two real problems: a placeholder album tag
  (`Audio CD`) beat a meaningful folder name, and an Admin correction to title, language or artwork
  was silently reverted by the next preparation because only `kind` carried an override flag. Fixed by
  bounding interpretation rather than growing it — a closed placeholder set, an `overrides` set of
  field names preparation never recomputes, and the **Magic Budget**: one explainable sentence is the
  admission price for any inference rule. Series stays uninferred. `ae2fe54`.
- `PRODUCT_FOUNDATION.md` P26 and `docs/product/MEDIA_CONVENTIONS.md` carry that outward; the latter
  is the one-page answer to "how do I organise files so AQENO understands them".
- **ADR 0029's code is deliberately not written.** The ADR 0028 implementation worker owns
  `application/ingestion.py`, `domain/content.py` and `ports/persistence.py` right now, and the
  override carry-over has to live inside the preparation pass it is rewriting. The remaining work is
  small: the placeholder constant, one inserted test in the title chain, `overrides` replacing
  `kind_overridden` with a forward-only migration, two provenance fields and `needs_review`.
- Created the **AQENO Adversarial Verifier** as a permanent role, `docs/agents/ADVERSARIAL_VERIFIER.md`
  — independent adversarial review at stable checkpoints only, read-only for production code during
  its primary pass, with "every escaped defect must pay rent" as a standing principle. **Defined and
  not executed:** implementation is in progress, which is precisely the condition under which the role
  forbids itself to run.
- No code changed in any of this. Documentation only, so the gates were not re-run; the last recorded
  green state stands at `1141 passed, 1 deselected`.

### 2026-08-19 — the approved visual direction was implemented

- Implemented the approved visual reference across the Device UI. This was an implementation pass,
  not a design exploration: no surface, navigation path, control meaning or capability changed, and
  nothing was routed that was not routed before.
- **The screens are now composed, not drawn.** `Theme.qml` holds every token, and one set of shared
  primitives carries the language: `PremiumSurface`, `ContentCard`, `ArtworkFrame` + `RoundedCorners`,
  `ArtworkGlow`, `ProgressTrack`, `ProgressRing`, `PageIndicator` and `AqenoGlyph`. Home and Browse
  use the *same* card, because showing an area and showing a work are the same act.
- **The rendering budget was treated as a product constraint.** RH1 is a Raspberry Pi 4, so every
  effect was built from the cheapest primitive that reaches the same perception. There is no realtime
  blur, drop shadow, shader effect, offscreen layer or particle system anywhere in the Device UI —
  verified by search, not by intention. Depth is luminance and layering; artwork ambience is
  concentric translucent geometry driven by a dominant colour the Python model computes once per
  cover and caches; the halo on the design targets is a radial gradient painted once and held as a
  texture; rings are `QtQuick.Shapes` arcs; celebration is seven declarative items.
- **Nothing that is animated is animated through a repaint.** Both glows take their brightness from
  the item's opacity rather than from their own paint or from per-band colour bindings, so fading
  light costs one node property per frame instead of a texture upload or sixteen re-evaluated
  bindings.
- Two rendering realities are recorded in `DEVICE_UI_BLUEPRINT.md § Visual language` rather than left
  in the code: `clip` on this Qt build is rectangular, so rounded artwork corners are *covered* in
  the surrounding colour; and `font.families` does not exist in this PySide6 build, so the font
  fallback chain is a single family.
- Icons are drawn in `AqenoGlyph` instead of bundled from Lucide. That keeps one weight and one
  softness across the set and avoids a dependency decision; the blueprint's "outline vector assets"
  intent stands and the amendment says so explicitly.
- Reviewed as rendered images at both viewports, which is how the overflow in the alarm and timer
  targets, the ring cutting behind the sender portrait and the volume overlay's dialog-like
  proportions were found. Fixed all three.
- Verification: `1180 passed, 1 deselected`. Ruff check and format green over `src/aqeno/ui` and
  `scripts`. The repository-wide `ruff check .` currently reports four unused imports in
  `application/ingestion.py`, which belongs to the in-flight ADR 0028 implementation and was left
  untouched.
- **Not verified: anything about frame rate.** The cost argument above is structural. Measuring it
  needs RH1, and the offscreen grab path used for screenshots reports no scene-graph timings.

## Next action

Each item is labelled **[hardware]** (needs the assembled box), **[architect]** (needs a product or
architecture decision) or **[delegable]** (bounded implementation; what it needs specified up front
is stated with it).

1. **[hardware]** Wait for delivery, then run the **seven-phase hardware smoke test** in
   `RH1_VALIDATION_CHECKLIST.md` before any further implementation: I²C → controls → blind operation
   → mechanics → knobs → light → tag-reader identification. Then the documented
   stereo/control/offline acceptance sequence, with measured evidence.
2. **[hardware]** Supply the canonical AQENO SVG and resolve G24's real DSI adapter before enabling
   the Plymouth presentation and measuring splash-to-first-frame handover.
3. **[hardware]** Fit three Cherry MX switches as PREVIOUS, NEXT and HOME on NeoKey sockets 0, 1 and
   3, leaving socket 2 empty, and verify the layout and blind findability.
4. **[delegable, after Phase 1 passes]** Write the **Qwiic Twist input adapter** for SELECT. It is
   the one clearly bounded implementation task waiting. Specify up front: it implements
   `PhysicalInputSource` exactly as `adapters/input/i2c_seesaw.py` does, reports
   `LogicalControl.SELECT_ENCODER` with rotate-left/right plus short and long press, imports its
   driver lazily inside an `open_*` function so the headless Core never sees it, uses I²C address
   `0x3F`, normalises direction so clockwise is forward before anything above the adapter sees it,
   reuses `PressGestureRecognizer` for the 800 ms threshold, and gets deterministic tests with an
   injected fake device — no sleeps, no hardware in unit tests. Out of scope: the RGB LED, any
   change to `MappedInputBus`, and any new port. Do not write it before the board is physically
   present and its address is confirmed on the assembled bus.
5. **[architect]** Open UX questions that only real use can answer: whether HOME removes the need for a BACK control
   once browsing is deeper than one level (ADR 0026 § 4), what counts as a "section" per content
   kind, whether focus wrapping reads as helpful or confusing to a three-year-old, and the design
   conflicts C1–C5 in `INTERACTION_MATRIX.md` § 9.
6. **[delegable, with review]** Documentation consolidation, when there is a natural occasion: `docs/DOCUMENTATION_GAPS.md` is
   now mostly historical — 11 of 24 gaps are marked closed, 2 deferred by intent, and several open
   ones (G08 failure taxonomy, G16 roadmap contradiction, G20 language convention) were overtaken by
   documents that now exist. The proposal is to move the genuinely live items to their owning
   documents — G24 to `HANDOVER.md`/`ROADMAP.md`, G21 to `NFC_REFERENCE_CANDIDATE.md`, G15 to
   `DEVICE_UI_PRINCIPLES.md`, G10 to `FAILURE_STATES.md` — and reduce the file to a short historical
   note. G17 (duplicate `## 12.` in `PRODUCT_FOUNDATION.md`) needs one deliberate renumbering pass
   because other documents cite those section numbers; it should not be half-fixed in passing.

## Handover to another agent

Read in this order: `ONBOARDING.md` → `AGENTS.md` → this file. `AGENTS.md` is the operating
contract and its authority order settles conflicts.

Three things that are easy to get wrong here, in the order they usually go wrong:

1. **A drawn screen is not a capability.** `scripts/ui_preview/` holds design targets for the clock,
   timer, alarm, messages and context actions. They are outside `src/`, unreachable from `Main.qml`,
   and tested to stay that way. Do not route them, do not add them to Home, do not build domain
   behaviour because a picture exists.
2. **Do not decide by committing code.** Technology, domain boundaries, platform contracts and
   product rules need an ADR first. Open questions — C1 snooze, C2 blind timer cancel, C3–C6,
   retention default, message deletion interaction, device context actions — are open on purpose and
   listed in `INTERACTION_MATRIX.md` § 9. Report a conflict instead of resolving it quietly.
3. **The procurement freeze is real.** `BUY NOW = nothing` until the ordered parts arrive and the
   smoke test has run. `INVENTORY.md` is the only place that records what exists.

Verification before reporting done, run bare and never through a pipe (`MISTAKES.md` M-004):

```bash
ruff check . && ruff format --check . && mypy src/aqeno/domain src/aqeno/application src/aqeno/ports && pytest
```

Device UI work additionally needs a look at the rendered output, not only at QML source:

```bash
python scripts/device_ui_screenshots.py --out build/ui        # the real surface
python scripts/device_ui_preview.py --out build/ui-preview    # the design targets
```

## Standing reminders

- Run quality commands directly, never through a pipe (`MISTAKES.md` M-004).
- Preserve unrelated user changes and keep commits conceptually narrow.
- Every AI-authored commit needs an honest `Co-Authored-By` trailer (ADR 0006 § 7).
- Push only on the maintainer's explicit instruction.
- Remaining hardware-only questions include true panel OFF/display-server behaviour, wake/startup
  timing and calibrated child volume. Do not fabricate results without Reference Hardware.
- At the next stable milestone, run the AQENO Adversarial Verifier
  (`docs/agents/ADVERSARIAL_VERIFIER.md`). Not while implementation of the reviewed area is active,
  and not as a background job.
