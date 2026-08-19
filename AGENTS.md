# AGENTS.md — AQENO Player

This file is the primary operating contract for AI coding agents working in this repository.

## Mission

Build AQENO as **a calm everyday companion for audio, time and personal connection** (ADR 0023) on
an open, adaptive, audio-first platform. The first focus is AQENO Kids; AQENO Easy must remain
possible from the same core.

Read `PRODUCT_FOUNDATION.md` before proposing or implementing product behaviour.

## Productive work only

This project is worked on productively. **No bells and whistles that do not advance the project.**

- Build what the current milestone requires, nothing beyond it.
- No abstraction, configuration option, theme, animation, metric, dashboard or plugin mechanism
  that no scoped use case asks for.
- No documentation about features that `docs/product/MVP.md` lists as out of scope.
- No unrequested reports, summaries or status files.
- Polish is not a deliverable until the thing works.

When in doubt whether something advances the project: it does not. Ask instead of building it.

## Deciding what to build

AQENO is built to be excellent, not to justify a business (ADR 0015). The test for a capability is
therefore **not** whether it differentiates AQENO from another product. It is:

> **Does this make AQENO meaningfully better for the person using it?**

with the companion test: **does it make AQENO better, or merely bigger?** "Optimal does not mean
maximal" — the section above still governs, and a capability that adds scope without adding value,
better interaction or a genuinely new possibility is declined or recorded in
`docs/product/FUTURE_PRODUCT_CONCEPTS.md`.

**First gate — the three pillars (ADR 0023).** A capability qualifies for consideration only if it
supports **AUDIO**, **TIME** or **PERSONAL CONNECTION**, and is compatible with a calm,
non-distracting device. One that supports none of them is declined without further analysis, and
passing the gate grants consideration rather than implementation.

When a product or feature question needs deciding, work through these in order:

1. **Real user value** — does it make actual use better?
2. **Simplicity** — does AQENO stay understandable?
3. **Quality** — can it feel like an integral part of the device?
4. **Architectural fit** — does it sit cleanly in the existing model?
5. **Broader vision** — does it needlessly foreclose future use situations?
6. **Competitor learning** — how do others solve this, and what can we take from it?
7. **Product potential** — only last: might this matter commercially later?

Point 7 may not dominate points 1–5. Two things that are **never** arguments on their own:

- *"A competitor already has this"* — existing products are benchmarks, not judges of what AQENO may
  contain. See `docs/product/COMPETITIVE_REVIEW.md`, which is a learning reference and carries no
  authority over scope.
- *"This is not a USP"* — that says nothing about whether it makes AQENO better.

The current primary design case is a child using AQENO independently in daily life on the reference
hardware. Other audiences in `PRODUCT_FOUNDATION.md` § 4 and § 14 are design horizon, not
implementation requirements for 1.0.

## Vibe-coding operating model

This is intentionally an AI-assisted / vibe-coding project. Fast iteration is desirable, but **speed must not replace explicit decisions, tests or maintainability**.

Agents should:

1. inspect existing code/docs before changing them;
2. make the smallest coherent change that advances the current goal;
3. state assumptions in code/docs rather than silently inventing product behaviour;
4. prefer boring, readable technology over clever abstractions;
5. keep commits/changes conceptually narrow;
6. add or update tests for behaviour changes;
7. update documentation when architecture or product contracts change;
8. never silently weaken privacy, offline behaviour, accessibility or hardware independence;
9. leave the repository in a runnable state;
10. surface uncertainty instead of fabricating APIs, hardware behaviour or licensing facts.

## Code quality

Code follows from AQENO's domain and documented decisions, not from generic patterns or a software
template.

- Use established domain vocabulary consistently. Prefer a precise AQENO term over generic
  `Helper`, `Service`, `Handler` or catch-all `Manager` names. `Manager` remains correct where it
  denotes AQENO's defined user role.
- Respect the existing architecture before introducing a new pattern or layer.
- Add an abstraction only for a concrete current need. Do not add speculative extension points.
- Reuse an existing abstraction when it already expresses the behaviour; do not copy its shape
  under a new name.
- Keep refactorings local and changes small enough that their motive remains reviewable.
- Comments explain why, a constraint, an invariant or a non-obvious decision. They do not restate
  straightforward code in prose.

## Authority order

When instructions conflict, use this order:

1. explicit current human instruction;
2. accepted ADRs in `docs/decisions/`;
3. `PRODUCT_FOUNDATION.md`;
4. `ARCHITECTURE.md`;
5. `ROADMAP.md`;
6. implementation convenience.

If a requested implementation conflicts with levels 2–4, flag the conflict before encoding a new long-term assumption. If the human confirms the change, update the relevant document/ADR with the implementation.

## Non-negotiable product constraints

- Local-first core playback.
- Core playback must not require a subscription or cloud account.
- Content must not be locked into AQENO.
- Playback and visual state are independent.
- Fast startup and wake are product requirements; optional services must not block local readiness without necessity.
- Ambient/photo-frame behaviour is explicit and permissioned, never the default idle fallback for child profiles.
- Dark-room operation must be possible with display and lights fully off.
- Frequent playback actions must remain physically operable.
- The child-facing experience must not optimise for engagement time.
- No ads or paid placements in child-facing UI.
- The device must never present unavailable capabilities as locked, disabled or purchasable.
  Unavailable capability means no UI surface; the local Core must feel complete.
- Guardian functionality must favour care over surveillance.
- NFC is optional and open; it must not become a proprietary content lock.
- Treat physical tags as brand-neutral triggers for AQENO-local assignments. Never infer permission
  or implement proprietary content extraction from a recognised third-party object.
- Hardware-specific code must be isolated behind platform interfaces.
- **No function and no navigation path may require touch** (ADR 0024). Touch is an optional
  capability; `touch = true` never means "use touch as the primary UI".
- Volume stays volume and Play/Pause stays Play/Pause: a volume control must never become
  contextual navigation. **Every control means one thing in every state** (ADR 0026 § 2). PREVIOUS
  and NEXT are content order and never navigate; HOME is the one always-available way out.
- **Everything essential works without looking** (P21), controls are told apart by hand (P22),
  accessibility comes from ordinary design rather than a special edition (P23), and light assists
  operation without ever defining it (P24). **DARK means zero visible light.**
- **Normal everyday operation must not require long-press or double-press gestures** (ADR 0024 § A2).
  Long press stays available for setup, service and hardware cases only, and no default binds it.
- Prefer inherent physical feedback over invented feedback (`PRODUCT_FOUNDATION.md` P20). Do not add
  a sound to a physical action whose result already speaks for itself.
- AQENO does not compete for attention (`PRODUCT_FOUNDATION.md` P19). No engagement loop, artificial
  badge, permanently changing content or unnecessary notification.
- No development toward a news feed, weather dashboard, browser, app store, games, social feed,
  advertising or a general information dashboard.

## Architecture rules

- Keep **domain/application logic hardware-agnostic**.
- Keep UI presentation separate from playback/content domain state.
- Treat content identity independently from source and launch method.
- Model roles as User / Manager / Owner, not Parent / Child in core domain code.
- Model adaptive UI through capabilities/configuration, not duplicated Kids/Easy applications.
- Model Actions and Scenes as first-class domain concepts when implemented.
- External/cloud integrations are adapters, never prerequisites for core domain operation.
- Prefer explicit interfaces at hardware boundaries: audio, display power, controls, NFC, connectivity, storage and power state.
- Keep the in-process Qt Quick/QML Device UI separate from a future Management UI. QML presents
  application state and emits intentions; it does not contain product rules or call adapters.

## Dependency policy

Before adding a dependency, verify that it:

- materially reduces complexity;
- has a compatible license for potential commercial distribution;
- is maintained enough for the role it will play;
- does not unnecessarily force cloud/network dependence;
- can be replaced behind an adapter if it is infrastructure-specific.

Record consequential dependency choices in an ADR.

## Security and privacy

- Do not collect data merely because it is technically available.
- Default to minimum retention.
- Never expose management interfaces unauthenticated beyond a deliberately trusted local setup flow.
- Do not commit secrets, tokens, credentials, private certificates or production identifiers.
- Treat child-related data as particularly sensitive even when a prototype runs locally.

## UI rules

- Kids Early must be usable without reading.
- Fundamental playback must not require the screen.
- Touch targets must be large and forgiving.
- Avoid modal dead ends and technical error language in user-facing UI.
- Do not illuminate the display merely because playback state changed.
- Physical controls must remain meaningful when the display is off.
- Do not wake the display for routine playback events, metadata changes or background service activity.
- For Kids profiles, default inactivity behaviour during playback is visual quiet/off, not ambient animation.
- Treat Ambient as a first-class display state with explicit authorisation and approved content sources.
- Accessibility and reduced-complexity modes are product architecture, not cosmetic themes.
- Build navigation and actions from available capabilities. Do not render locked controls,
  premium badges, upgrade prompts or other on-device upsell surfaces.
- Keep complex administration and free-text entry off the appliance UI. Do not add Qt Virtual
  Keyboard or a replacement keyboard without a new, explicit product decision.
- Apply `docs/product/DEVICE_UI_PRINCIPLES.md` before adding a Device UI element: prefer physical
  interaction, shallow navigation, one contextual primary action and removal of unnecessary UI.
- Design encoder-first, never touch-first with encoder support bolted on. Every state must make
  visible where focus is, what rotation does and what a press does, at normal viewing distance.
- `docs/implementation/INTERACTION_MATRIX.md` is normative for what each control does in each
  situation. A surface that would need a control to mean something new, a sixth control, a long
  press, a double press or touch is a **design conflict to report**, not to implement.

## Testing expectations

At minimum, protect these invariants when the relevant modules exist:

- local content plays without internet/cloud;
- playback continues when visual output sleeps;
- physical volume/playback commands work with display off;
- content resume is independent of launch method;
- unsupported hardware fails clearly rather than partially pretending to work;
- the whole everyday journey is operable without a single touch event;
- role/Guardian boundaries cannot be bypassed through ordinary UI flows;
- display remains off through routine playback transitions when policy requires it;
- startup/wake timing can be measured on Reference hardware and regressions are surfaced.

Prefer deterministic unit tests for domain logic and a small number of integration tests at hardware/service boundaries.

## Documentation discipline

- New durable product rule → update `PRODUCT_FOUNDATION.md` or add an ADR.
- New architectural decision/trade-off → add an ADR.
- New milestone/scope change → update `ROADMAP.md`.
- New hardware support → document its compatibility level and known limitations.
- Display-state or ambient-mode changes → update `docs/product/DISPLAY_BEHAVIOR.md` when the contract changes.
- Do not let README become the architecture document.
- **Consolidation before fragmentation.** Create a new canonical document only when no existing one
  offers a sensible home for the decision; prefer a dated amendment or a new section in the document
  that already owns the subject. Consolidate historical or superseded documentation when you are
  already working in it.

## Definition of done

A change is done when:

- behaviour matches the current product/architecture contracts;
- relevant tests pass;
- no obvious dead code or temporary debug output remains;
- user-visible failure states are understandable;
- docs are updated when contracts changed;
- the next agent can understand why the code is shaped this way.


## Required implementation specs

Before implementation, read:
- `docs/product/MVP.md`
- `docs/product/USER_JOURNEY_KIDS_EARLY.md`
- `docs/product/DISPLAY_BEHAVIOR.md`
- `docs/product/DEVICE_UI_PRINCIPLES.md`
- `docs/product/DEVICE_UI_BLUEPRINT.md`
- `docs/implementation/DOMAIN_MODEL.md`
- `docs/implementation/PLATFORM_CONTRACTS.md`
- `docs/implementation/DISPLAY_STATE_MACHINE.md`
- `docs/implementation/CONFIGURATION_DEFAULTS.md`
- `docs/implementation/CONTENT_INGESTION.md`
- `docs/implementation/READINESS_STATES.md`
- `docs/implementation/FIRST_VERTICAL_SLICE.md`
- `docs/implementation/INTERACTION_MATRIX.md`
- `docs/hardware/HARDWARE_REFERENCE.md`
- `docs/management/LOCAL_MANAGEMENT_API.md` when changing management/application boundaries

The first implementation target is `FIRST_VERTICAL_SLICE.md`. Do not broaden the scope without an explicit roadmap/ADR decision.
