# ADR 0015 — Excellence first, product optional

**Status:** Accepted
**Date:** 2026-08-18
**Accepted:** 2026-08-18

> **AQENO is built to be excellent, not to justify a business.**

## Context

On 2026-08-18 a competitive review examined AQENO against twelve existing products and asked whether
it has enough independent product value to exist. It is recorded in
`docs/product/COMPETITIVE_REVIEW.md`. Its findings are sound and are kept.

Its *framing* was wrong for this project, and that became visible only once the analysis existed. The
review judged every capability by whether it differentiates AQENO in a market. That is the correct
question for a company deciding what to fund. It is the wrong question here, and left unchallenged it
would have produced concretely bad decisions — dropping a display because a competitor uses a smaller
one, declining to build reliable resume because everyone has it, treating a feature's existence
elsewhere as a reason not to build it well.

The actual situation is simpler than the review assumed. AQENO is being built because the maintainer
wants an exceptionally good audio player made to his own design, and the first one is for a specific
child in his own family who will use it every day. That is a real user with real requirements, not a
hypothetical market segment.

Historically, CD players, MP3 players, radios and telephones existed in large numbers with nearly
identical core functions. They earned their place through combinations of handling, design, build
quality, reliability, feel, price, scope, integration and personal preference — not through
functional novelty. There is no obligation to innovate.

## Decision

### 1. The motivation is excellence for real use, not differentiation

AQENO does not have to justify its existence against Toniebox, Phoniebox, Yoto, hörbert, enna, Alexa,
tablets or any other player. The measure is whether AQENO is excellent for the people actually using
it.

**Optimal does not mean maximal.** Every feature still has to earn its place, and YAGNI stays binding
(`AGENTS.md` § "Productive work only"). The question changes, though, from *"is this a USP?"* to:

> **Does this make AQENO meaningfully better for the person using it?**

with the companion test: *does it make AQENO better, or merely bigger?* A capability that adds scope
without adding real value, better interaction or a genuinely new possibility is still declined or
recorded as a future concept.

### 2. Competitors are benchmarks and teachers, never judges of existence

`COMPETITIVE_REVIEW.md` is reclassified as a **benchmark and productization reference**. Its questions
become:

- what does this product solve outstandingly well?
- what should we learn from it?
- what works badly in daily use?
- what would we do differently for AQENO?
- which proven solution should we not reinvent for no reason?

**"Not a USP" never means "do not build".** NFC, resume, internet radio, podcasts, physical controls,
a good display and a sleep timer are all commodity in this market and all remain legitimate parts of
AQENO. The review's kill list survives as an honest record of *what does not differentiate us*, and
carries no authority over what gets built.

### 3. The primary design case is one child; the design horizon is broader

**Primary design case:** a child uses AQENO independently, intuitively, safely and with pleasure, in
daily life, on the reference hardware.

This real case outranks hypothetical market requirements in every current decision. What it demands is
already documented and unchanged: immediately understandable operation, fast response, quick and
appropriate boot behaviour, robust playback, good feel, physical operability, visual orientation, good
audio quality, sensible offline behaviour, resume, easy content selection, NFC as an immediate
interaction, no unnecessary visual attention, a display that dims and switches fully off, bedroom-safe
behaviour, no distracting LEDs, understandable failures, and no visible Linux or computer feeling.

**This does not make AQENO a children's box.** The broader vision in `PRODUCT_FOUNDATION.md` § 4 and
§ 14 stands — children of different ages, adults, a kitchen player, older people, people with motor or
other accessibility needs, and the case where administration and daily use belong to different people.
Those are **design horizon**, not simultaneous implementation requirements for AQENO 1.0. We are not
building five products at once.

### 4. Hardware and interaction are decided by use, not by comparison

The 7-inch touchscreen, the rotary encoder, the physical keys and the planned NFC exist and are to be
**tried in practice**. It is not concluded from a competitor comparison that 7 inches is too large,
that a display is unnecessary, or that a small pixel display would be sufficient.

Real use answers these instead: how do large covers work, can a child recognise content visually, is
browsing pleasant, does the display distract during listening, when should it disappear, how useful is
touch, which functions genuinely benefit. Future AQENO hardware may then need a different display
format — decided by experience, not by analogy.

The same applies to the four interaction paths. They are tested rather than declared redundant. For
each function we still ask which path is genuinely best in that situation; we do not create artificial
redundancy, and **unassigned keys may stay unassigned**.

### 5. Own core over adopting an existing one, on design grounds

Building on Phoniebox may still be examined technically. It is not settled by Phoniebox having a
similar feature set, and AQENO does not have to prove that Phoniebox is *incapable* of the same
functions.

A dedicated core is justifiable by control over the whole system, a consistent domain model, a defined
UX, appliance behaviour, hardware integration, maintainability, the intended architecture, freedom to
experiment and the longer-term AQENO vision. The question is which basis is better **for the device we
want to build**.

### 6. Commercialisation is optional and does not shape today's decisions

AQENO is not required to become a product. Current work does not optimise for sales, investors,
subscription revenue, market size, USP marketing, retail, minimal series BOM, CE certification,
support cost or OEM partners. Those may be documented and kept open where a technical decision can do
so at no cost — **they may not degrade the quality of the reference device**.

`Send to AQENO` in particular is no longer tied to monetisation. A parent sending a child a personal
audio message from a trip, a heart appearing, a tap, a familiar voice — that is sufficient personal
value on its own. Whether an AQENO Connect service ever follows is a later, separate decision.

If it later turns out that other people want AQENO too, a **separate productisation phase** examines
audiences, market, unit cost, series hardware, regulation, liability, support, distribution,
monetisation and business model. `ROADMAP.md` P5 is that phase and stays where it is.

### 7. Product optional does not mean engineering optional

Clean architecture, tests, ADRs, traceable decisions, a legible commit history, hardware abstraction,
clear responsibilities, documented assumptions, reproducible reference hardware, robust failure
handling, and security and privacy by design all remain in force. That discipline is what keeps a
later productisation possible without developing for a hypothetical market today.

### 8. Decision order for product and feature questions

1. **Real user value** — does it make actual use of AQENO better?
2. **Simplicity** — does AQENO stay understandable, or does complexity grow without cause?
3. **Quality** — can it be built so that it feels like an integral part of the device?
4. **Architectural fit** — does it sit cleanly in the existing model?
5. **Broader vision** — does it needlessly foreclose future use situations?
6. **Competitor learning** — how do others solve this, and what can we take from it?
7. **Product potential** — only last: might this matter for a commercial product later?

Point 7 may not dominate points 1–5.

### 9. Real use is a source of evidence

The reference prototype is explicitly a learning instrument. Observations from real use are recorded
in `docs/product/USE_OBSERVATIONS.md` and **may overturn existing product assumptions**, including
assumptions in `PRODUCT_FOUNDATION.md` and in this ADR.

## Alternatives considered

**Keep the market frame and narrow AQENO to its two differentiating advantages.** The competitive
review's own recommendation, and correct for a product seeking a market. Rejected because the premise
does not hold: there is no market to enter, there is a child who will use this device. Narrowing to
what differentiates would have removed capabilities that the actual user needs — a display, podcasts,
radio, a sleep timer — for reasons that have nothing to do with him.

**Drop the competitive review entirely.** Rejected. Its research is accurate and its observations
about what competitors do outstandingly well are the most useful part of it. Deleting it would also
destroy the record of *why* the framing changed, which is the substance of this ADR.

**Say nothing and simply proceed.** Rejected because the review is now in the repository, is written
persuasively, and would be read by a future contributor or agent as binding guidance. An unrebutted
document is an instruction.

## Consequences

**Easier.** Feature decisions become answerable from the device itself rather than from market
research. The display, the encoder, the keys and NFC can be evaluated by use rather than defended by
argument. Future concepts survive without needing a business case, which is what they were always for.

**Harder.** "Does this make AQENO better?" is a weaker filter than "is this a USP?", so the discipline
against scope growth now rests entirely on `AGENTS.md` § "Productive work only" and on point 2 of the
decision order. The risk this ADR creates is feature accumulation justified as quality, and it should
be watched for.

**Constrained.** Point 7 of the decision order is subordinate: no current design may be shaped by a
hypothetical commercial requirement. Conversely § 7 forbids using "it is only personal" as an excuse
for weaker engineering.

**Documents affected.** `PRODUCT_FOUNDATION.md` gains the canonical motivation and drops its defensive
framing against the Toniebox; `AGENTS.md` gains the decision order; `COMPETITIVE_REVIEW.md` is
reclassified; `FUTURE_PRODUCT_CONCEPTS.md` records that absent differentiation is not grounds for
removal; `USE_OBSERVATIONS.md` is created. No ADR is superseded and no concept is deleted. The
concrete conflicts found during that review are listed in `COMPETITIVE_REVIEW.md` § Conflicts.

**Not decided here.** Nothing about architecture, scope of the current vertical slice, hardware
selection or the roadmap changes as a consequence of this ADR. It changes the criteria by which the
next decisions are judged, not the decisions already made.
