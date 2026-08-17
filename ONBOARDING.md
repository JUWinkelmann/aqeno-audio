# Onboarding — AI Assistants

Read this first. It takes you from zero to productive without re-deriving the project.

## 1. What AQENO is, in three sentences

AQENO is an open, adaptive, audio-first player platform. First focus is **AQENO Kids** (a
three-year-old must be able to operate it without reading); the same core must be able to serve
**AQENO Easy** later. Audio playback and visual output are architecturally independent — the
device must be fully usable in a completely dark room with display and all LEDs off.

## 2. Where the project actually stands

- **Phase:** documentation complete enough to start, **no code, no version control, no ADRs.**
- **Declared next implementation target:** `docs/implementation/FIRST_VERTICAL_SLICE.md`.
- **But it is blocked:** no language/runtime, UI stack, audio engine, persistence or local
  event-channel decision exists. See `docs/DOCUMENTATION_GAPS.md` for the blocking list.

Do not start writing production code until the blocking gaps are closed by ADRs. Writing code
first *is* the decision — and it would be an undocumented one.

## 3. Reading order

Do not skim these. They are contracts, not background.

| # | Document | Why |
|---:|---|---|
| 1 | `AGENTS.md` | Your operating contract, authority order, definition of done |
| 2 | `PRODUCT_FOUNDATION.md` | Product principles P01–P14, dark-room requirement, roles |
| 3 | `ARCHITECTURE.md` | Layer boundaries, ports, staged startup, open decisions |
| 4 | `docs/product/MVP.md` | What is in scope and explicitly out |
| 5 | `docs/product/USER_JOURNEY_KIDS_EARLY.md` | The experience the code must produce |
| 6 | `docs/product/DISPLAY_BEHAVIOR.md` | Display state machine and its rules |
| 7 | `docs/implementation/DOMAIN_MODEL.md` | Entities and invariants |
| 8 | `docs/implementation/PLATFORM_CONTRACTS.md` | Ports: input, display, LED, audio, persistence |
| 9 | `docs/implementation/FIRST_VERTICAL_SLICE.md` | The first thing to build, in order |
| 10 | `docs/hardware/HARDWARE_REFERENCE.md` | Reference prototype, solderless constraint |
| 11 | `MISTAKES.md` | Mistakes already made. Do not repeat them. |
| 12 | `docs/DOCUMENTATION_GAPS.md` | What is not yet decided — read before assuming |
| 13 | `docs/decisions/` | Accepted ADRs override `ARCHITECTURE.md` |

## 4. How work is done here

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

## 5. Non-negotiables you will be tempted to break

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

## 6. Conventions

- **Documentation and code are English.** Conversation with the maintainer may be German.
- **Root docs are UPPERCASE.md**; `docs/` is grouped by `product/`, `implementation/`,
  `hardware/`, `decisions/`.
- **ADRs:** `docs/decisions/NNNN-short-title.md`, template in `docs/decisions/README.md`.
- **Timestamps in docs are absolute dates**, never "today" or "last week".

## 7. Before you report finished

Check `AGENTS.md` § "Definition of done", plus:

- Did I change behaviour without a test?
- Did I fix a decision without an ADR?
- Did I add something `MVP.md` does not ask for?
- Would the next assistant understand *why* the code is shaped this way?
- Did I log a new mistake in `MISTAKES.md` if one happened?
