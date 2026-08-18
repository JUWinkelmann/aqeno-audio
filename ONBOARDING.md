# Onboarding — Architects and AI Assistants

Read this first. It takes you from zero to productive without re-deriving the project.

## 1. What AQENO is, in three sentences

AQENO is an open, adaptive, audio-first player platform. First focus is **AQENO Kids** (a
three-year-old must be able to operate it without reading); the same core must be able to serve
**AQENO Easy** later. Audio playback and visual output are architecturally independent — the
device must be fully usable in a completely dark room with display and all LEDs off.

## 2. What this project is for

**AQENO is a personal project. The maintainer is building it for his son.**

That is the actual purpose, and it decides what matters. The product vision in
`PRODUCT_FOUNDATION.md` is real and worth building toward, but nobody is waiting on a release, and
there is no business behind it.

> **AQENO is built to be excellent, not to justify a business.**

The full statement of motivation is `PRODUCT_FOUNDATION.md` § 0, decided in ADR 0015. Two rules from
it you will need immediately: a capability does not have to be unique, it has to make AQENO better for
the person using it; and existing products are benchmarks, never reasons to leave something out.

**Deferred by intent — do not treat these as live constraints:**

- licensing (`ADR 0004`, `ADR 0006` — both **on hold**, retained as a record of the reasoning);
- commercialisation, trademark, regulatory compliance, GDPR;
- publication of the repository, and therefore contributor agreements.

If work would only make sense for a released product, it is out of scope. Ask before doing it.

**One thing survives that deferral and is not negotiable:** volume limiting for child profiles is a
real hearing-protection requirement, because the device is for an actual three-year-old. It was
briefly justified by liability reasoning; the better reason stands on its own.

## 3. Where the project actually stands

- **Phase:** the First Vertical Slice is implemented and desktop-tested; RH1 hardware validation is
  the active boundary.
- **Current continuation:** read `HANDOVER.md`. Step 10 has an implemented encoder/NeoKey adapter;
  remaining work needs the assembled prototype, exact hardware evidence or a scoped new decision.
- **Technology basis, all Accepted:** ADR 0001 Python 3.11+ · 0002 PySide6/QML in-process ·
  0003 GStreamer · 0005 DE/EN i18n · 0007 SQLite WAL + TOML settings · 0008 test strategy ·
  0009 content kinds.
- **How to set up, run and test:** `DEVELOPMENT.md`.
- **Closed implementation contracts:** input delivery, failure states, resume, readiness and content
  ingestion are specified and implemented.
- **Open physical decisions/evidence:** exact FREENOVE display revision and display-server path,
  authoritative panel off, final I2S wiring/audio behaviour, NFC selection, power, boot/wake timing,
  LED true-off behaviour and calibrated child volume.

Do not decide a technology by committing code. Writing code first *is* the decision, and it would be
an undocumented one.

## 4. Reading order

Do not skim these. They are contracts, not background.

| # | Document | Why |
|---:|---|---|
| 1 | `AGENTS.md` | Your operating contract, authority order, definition of done |
| 2 | `PRODUCT_FOUNDATION.md` | Product principles P01–P14, dark-room requirement, roles |
| 3 | `ARCHITECTURE.md` | Layer boundaries, ports, staged startup, open decisions |
| 4 | `docs/product/MVP.md` | What is in scope and explicitly out |
| 5 | `docs/product/USER_JOURNEY_KIDS_EARLY.md` | The experience the code must produce |
| 6 | `docs/product/DISPLAY_BEHAVIOR.md` | Display state machine and its rules |
| 7 | `docs/product/DEVICE_UI_PRINCIPLES.md` | Mandatory appliance-UI decision filter |
| 8 | `docs/implementation/DOMAIN_MODEL.md` | Entities and invariants |
| 9 | `docs/implementation/PLATFORM_CONTRACTS.md` | Ports: input, display, LED, audio, persistence |
| 10 | `docs/implementation/DISPLAY_STATE_MACHINE.md` | **Normative** transition table. Do not infer transitions from prose. |
| 11 | `docs/implementation/CONFIGURATION_DEFAULTS.md` | Every timeout, brightness and volume value. Never invent one. |
| 12 | `docs/implementation/CONTENT_INGESTION.md` | Library discovery, identity and metadata contract |
| 13 | `docs/implementation/READINESS_STATES.md` | Staged startup guarantees and degradation |
| 14 | `docs/implementation/FIRST_VERTICAL_SLICE.md` | Implemented slice contract and remaining RH1 boundary |
| 15 | `DEVELOPMENT.md` | Toolchain, layout, how to run and test |
| 16 | `docs/hardware/HARDWARE_REFERENCE.md` | Acquired prototype, topology and verification boundary |
| 17 | `HANDOVER.md` | Current live state and exact next action |
| 18 | `MISTAKES.md` | Mistakes already made. Do not repeat them. |
| 19 | `docs/DOCUMENTATION_GAPS.md` | Remaining known gaps; historical analysis is retained |
| 20 | `docs/decisions/` | Accepted ADRs override `ARCHITECTURE.md` |

Two further documents are **context, not contracts**: `docs/product/COMPETITIVE_REVIEW.md` records
what competing products do well and badly, and carries no authority over scope;
`docs/product/USE_OBSERVATIONS.md` collects evidence from real use and may overturn assumptions in the
list above.

## 5. How work is done here

**Productive work only.** No bells and whistles that do not advance the project. This is a
project rule, not a style preference — see `AGENTS.md` § "Productive work only".

Concretely:

- Do not build abstractions before a use case needs them.
- Do not add config options, themes, animations, dashboards, metrics or plugin systems that
  nothing in `MVP.md` asks for.
- Do not write documentation about features that `MVP.md` lists as out of scope.
- Do not produce reports, summaries or status files nobody asked for.
- If it does not move the current vertical slice forward, it does not get built.

**Decision discipline.** When your implementation would fix a technology choice, a domain
boundary, a platform contract or a product rule: stop, propose an ADR
(`docs/decisions/NNNN-short-title.md`), get confirmation. Do not decide by committing code.

**Uncertainty.** Surface it. Do not invent APIs, hardware behaviour, licence terms or product
rules. An honest "this is undecided, here are the two credible options" is worth more than a
plausible-looking guess.

## 6. Non-negotiables you will be tempted to break

These come from `AGENTS.md` and `PRODUCT_FOUNDATION.md`. Listed here because they are the ones
an assistant most often breaks by accident:

1. **No Pi-specific import in domain or application layers.** GPIO, I2C, board SDKs live only in
   adapters behind ports.
2. **Never equate playback state with display state.** A track change must not wake the display.
3. **Never wake the display for background activity** — metadata, buffering, sync, chapter change.
4. **True OFF must mean true OFF**, including user-facing LEDs, under Night/Dark-Room policy.
5. **Nothing in core playback may require network, cloud or an account.**
6. **Content identity is independent of source and of launch method.** Resume position belongs to
   content + profile, never to an NFC tag.
7. **No child-facing technical error text.** No URLs, HTTP codes, stack traces, Linux errors.
8. **Roles are User / Manager / Owner** in domain code, never Parent / Child.
9. **One adaptive core, not a Kids app and an Easy app.** Variation is capability configuration.
10. **No engagement mechanics.** No streaks, badges, autoplay-forever, notifications, ads.

## 7. Conventions

- **Documentation and code are English.** Conversation with the maintainer may be German.
- **Root docs are UPPERCASE.md**; `docs/` is grouped by `product/`, `implementation/`,
  `hardware/`, `decisions/`.
- **ADRs:** `docs/decisions/NNNN-short-title.md`, template in `docs/decisions/README.md`.
- **Timestamps in docs are absolute dates**, never "today" or "last week".

## 8. Before you report finished

Check `AGENTS.md` § "Definition of done", plus:

- Did I change behaviour without a test?
- Did I fix a decision without an ADR?
- Did I add something `MVP.md` does not ask for?
- Would the next assistant understand *why* the code is shaped this way?
- Did I log a new mistake in `MISTAKES.md` if one happened?
