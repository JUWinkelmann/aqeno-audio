# Mistakes Log

Purpose: record mistakes once so they are not repeated. Every AI assistant reads this during
onboarding (`ONBOARDING.md`) and appends to it when a mistake happens.

## How to use this file

- One entry per mistake, newest at the bottom of its section.
- Record the **mechanism** ("why it was easy to get wrong"), not just the fix. A fix without a
  mechanism does not prevent recurrence.
- Log a mistake even if you caught it yourself before it caused damage.
- If a mistake reveals a missing rule, also add the rule to `AGENTS.md` or an ADR and link it.
- Do not log ordinary iteration ("first draft was too long"). Log things that cost time, broke a
  contract, or would mislead the next assistant.

Entry format:

```markdown
### M-NNN — Short title
**Date:** YYYY-MM-DD
**Class:** process | architecture | product-rule | documentation | tooling | hardware
**What happened:**
**Why it was easy to get wrong:**
**Consequence:**
**Rule going forward:**
```

## Process and project setup

### M-001 — Documentation-only project ran without version control
**Date:** 2026-08-17
**Class:** tooling
**What happened:** Nine substantial specification documents were written and iterated without the
project being a git repository. There is no history, no way to see what changed between
`PRODUCT_FOUNDATION.md` v0.1 and v0.2, and no way to revert an AI-assisted edit.
**Why it was easy to get wrong:** Writing docs feels low-risk, so repository setup gets deferred.
The risk only becomes visible once an assistant rewrites a file badly.
**Consequence:** Any AI edit to a spec is irreversible. In an explicitly AI-assisted project this
is the single largest avoidable risk.
**Rule going forward:** `git init` before any further edits. Every AI-assisted change is committed
in a conceptually narrow commit so it can be reverted individually.
**Resolved:** 2026-08-17 — repository initialised, remote `git@github.com:JUWinkelmann/aqeno-audio.git`.
The nine original documents are committed as one baseline; their earlier history is unrecoverable.

### M-002 — Implementation declared "next" while its prerequisites were undecided
**Date:** 2026-08-17
**Class:** process
**What happened:** `AGENTS.md` and `CLI_START.md` instruct an agent to implement
`FIRST_VERTICAL_SLICE.md` as the first target. But no ADR exists for language/runtime, UI stack,
audio engine, persistence or the local event channel — and `ARCHITECTURE.md` explicitly lists all
of them as open. The same documents also forbid deciding these silently.
**Why it was easy to get wrong:** The slice document is well written and reads as actionable, so
the missing foundation underneath it is not visible from the document itself.
**Consequence:** Any agent following `CLI_START.md` literally must either stall or decide the
whole technology stack implicitly through its first commit — which is the failure mode the
authority order was designed to prevent.
**Rule going forward:** A document may only be declared the implementation target once every
decision it depends on is either recorded in an ADR or explicitly marked as free choice. See
`docs/DOCUMENTATION_GAPS.md`.

### M-003 — Roadmap phase and implementation documents contradict each other
**Date:** 2026-08-17
**Class:** documentation
**What happened:** `ROADMAP.md` places the project at P0 with P1 (UX discovery) and P2
(feasibility spikes) entirely unchecked, and states MVP scope should be frozen "only after P1/P2
evidence". Yet `docs/product/MVP.md` already freezes MVP scope and
`docs/implementation/FIRST_VERTICAL_SLICE.md` is declared the implementation target.
**Why it was easy to get wrong:** The documents were written in separate sessions and each is
internally consistent.
**Consequence:** An assistant cannot tell whether it should be doing discovery or implementation,
and `AGENTS.md`'s authority order does not resolve it (both are level 3–5).
**Rule going forward:** `ROADMAP.md` is the single source of truth for *which phase we are in*.
When implementation docs are created ahead of the roadmap, the roadmap must say so explicitly.

### M-004 — Verification pipeline hid a failing check
**Date:** 2026-08-17
**Class:** tooling
**What happened:** The pre-commit verification was run as
`ruff check . 2>&1 | tail -2 && mypy ... && pytest ... && git commit && git push`. In a shell
pipeline the exit status is the *last* command's, so `tail` returning 0 masked ruff's failure. The
`&&` chain continued, and a commit with a lint error was pushed. It was caught immediately, but only
because the output was read by eye — the automation had already reported success.
**Why it was easy to get wrong:** Piping through `tail` to keep output short is a natural habit when
a command is chatty, and the chain *looks* like it is gated on each step.
**Consequence:** A green-looking verification that verifies nothing. Worse than no check, because it
creates confidence rather than absence of it — the same failure mode as a boundary test that cannot
fail.
**Rule going forward:** Never pipe a command whose exit status gates the next step. Run the checks
bare, exactly as `DEVELOPMENT.md` § Before committing lists them, and read the exit codes:

```bash
ruff check . && ruff format --check . && mypy && pytest
```

If output needs shortening, capture it to a file and inspect afterwards — never in the gating chain.

## Architecture

_No entries yet._

## Product rules

_No entries yet._

## Hardware

_No entries yet._
