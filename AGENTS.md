# AGENTS.md — AQENO Player

This file is the primary operating contract for AI coding agents working in this repository.

## Mission

Build AQENO as an **open, adaptive, audio-first player platform**. The first focus is AQENO Kids; AQENO Easy must remain possible from the same core.

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
- Guardian functionality must favour care over surveillance.
- NFC is optional and open; it must not become a proprietary content lock.
- Hardware-specific code must be isolated behind platform interfaces.

## Architecture rules

- Keep **domain/application logic hardware-agnostic**.
- Keep UI presentation separate from playback/content domain state.
- Treat content identity independently from source and launch method.
- Model roles as User / Manager / Owner, not Parent / Child in core domain code.
- Model adaptive UI through capabilities/configuration, not duplicated Kids/Easy applications.
- Model Actions and Scenes as first-class domain concepts when implemented.
- External/cloud integrations are adapters, never prerequisites for core domain operation.
- Prefer explicit interfaces at hardware boundaries: audio, display power, controls, NFC, connectivity, storage and power state.

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

## Testing expectations

At minimum, protect these invariants when the relevant modules exist:

- local content plays without internet/cloud;
- playback continues when visual output sleeps;
- physical volume/playback commands work with display off;
- content resume is independent of launch method;
- unsupported hardware fails clearly rather than partially pretending to work;
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
- `docs/implementation/DOMAIN_MODEL.md`
- `docs/implementation/PLATFORM_CONTRACTS.md`
- `docs/implementation/DISPLAY_STATE_MACHINE.md`
- `docs/implementation/CONFIGURATION_DEFAULTS.md`
- `docs/implementation/FIRST_VERTICAL_SLICE.md`
- `docs/hardware/HARDWARE_REFERENCE.md`

The first implementation target is `FIRST_VERTICAL_SLICE.md`. Do not broaden the scope without an explicit roadmap/ADR decision.
