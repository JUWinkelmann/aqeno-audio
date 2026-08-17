# ADR 0006 — Non-commercial project posture, GPLv3, and liability minimisation

**Status:** Proposed — **ON HOLD**
**Date:** 2026-08-17
**Supersedes:** ADR 0004 (also on hold)

> **On hold as of 2026-08-17.** The maintainer has clarified the project's purpose: AQENO is being
> built for his own son. Nothing is distributed, published or sold, so neither product liability nor
> licence choice is a live question, and deciding either now would be premature. This ADR and
> ADR 0004 are retained as a record of the reasoning, to be revisited if publication or distribution
> ever becomes real.
>
> **Two things from this ADR remain in force**, because they stand without the legal argument:
> - **§ 6 volume limiting** — hearing protection for an actual child, now the primary reason rather
>   than a liability mitigation. The concrete values (gap G05) are still a prerequisite for the audio
>   step of the first vertical slice.
> - **§ 7 provenance discipline** — honest commit authorship and co-authorship trailers, which cost
>   nothing to maintain and are unrecoverable if neglected.
>
> **Two things become urgent only at publication**, and must be done *before* the repository is made
> public, not after: registering the `AQENO` trademark, and adding `CONTRIBUTING.md` with a
> contributor agreement. Until then the repository stays private.
>
> **One consequence to know before ADR 0002 is accepted** (raised 2026-08-17, on paid plugins): GPL
> without a linking exception, combined with ADR 0002's in-process coupling, largely forecloses
> proprietary third-party plugins — an in-process plugin is plausibly a derivative work. The ways out
> are a linking exception, a permissive licence, or out-of-process plugins over an arm's-length
> protocol, the last of which reintroduces the IPC and authentication surface ADR 0002 removed. No
> decision is needed now; it is noted because it is a door that closes quietly. Charging for plugins
> would additionally contradict `P02 Content, not apps` and `MVP.md`'s explicit exclusion of
> app-store style plugins, so it would require changing `PRODUCT_FOUNDATION.md`, not only the licence.
> A plugin *architecture* for content providers and hardware adapters raises none of this — the
> conflict is only with charging for them.
>
> The licence-driven restrictions in ADR 0004 § 5 do **not** apply while nothing is distributed:
> AAC/M4B, Qt Virtual Keyboard and the fuller GStreamer plugin sets are all available. ADRs 0002 and
> 0003 keep PySide6 and GStreamer on technical merit regardless.

> **Not legal advice.** This records the project's chosen posture and the engineering rules that
> follow from it, so that decisions stay consistent. The residual risks in § 6 and the uncertainties
> in ADR 0004 still warrant review by a qualified lawyer before any public release.

## Context

ADR 0004 kept the proprietary-commercial distribution path open, at a measurable price paid in the
MVP. The maintainer has since stated the governing requirement plainly:

> **No liability for anything.**

This is a stronger constraint than any technical or business preference in the project so far, and it
resolves several open questions at once — but not in the direction the earlier commercialisation
discussion assumed.

The decisive legal mechanism is the EU Product Liability Directive **2024/2853**, which treats
software as a product, including standalone software, but exempts free and open-source software
**developed and supplied outside a commercial activity**. The exemption is conditioned on
non-commerciality, not on the licence. Transposition by member states runs to the end of 2026.

The consequence is unavoidable and must be stated rather than glossed over: **liability minimisation
and revenue are mutually exclusive here.** Any sale — assembled devices, kits, printed enclosures,
support contracts, a certification programme, even a pre-flashed SD card — places a product on the
market, attaches CE/GPSR/ProdHaftG obligations to that product, and undermines the exemption that
this ADR relies on.

## Decision

### 1. AQENO is a non-commercial open-source project

AQENO generates **no revenue from any source**. Specifically excluded, and each was a live option
before this ADR:

- no sale of assembled devices, kits, enclosures, tokens, cables or any physical goods;
- no sale of pre-flashed SD cards or images;
- no paid support, warranty, consulting or installation;
- no hosted cloud service, subscription, or any paid tier;
- no "AQENO Compatible" certification programme, since certification is a quality statement that
  creates its own exposure;
- no content store, affiliate links or revenue share;
- no dual-licensing as an ongoing business — but see § 7, which deliberately preserves the *ability*
  to relicense, because that is what makes a later sale possible;
- no advertising or sponsorship placements in the software.

Voluntary donations are **not** adopted as part of this decision. Whether a donation channel
constitutes commercial activity for the purposes of the exemption is exactly the kind of edge this
posture exists to avoid. If it is ever wanted, it needs its own ADR and legal advice first.

### 2. Licence: GPLv3-or-later

AQENO is licensed **GPL-3.0-or-later**. It fits the project's own philosophy — open content, no
lock-in, bring your own hardware — and under this posture it costs nothing.

The interim constraint from ADR 0004 (no GPL code linked into the application) is **withdrawn**. Its
purpose was to preserve a path this ADR closes deliberately.

### 3. Constraints that now lift

Four costs recorded in ADR 0004 § Consequences disappear, and the affected ADRs are revised
accordingly:

| Previously excluded | Now |
|---|---|
| Qt Virtual Keyboard (GPLv3) | **Permitted** — no custom on-screen keyboard needs writing for `SETUP` |
| PyQt6 (GPLv3) | Permitted, but ADR 0002 **keeps PySide6** on technical merit: official binding, better QML integration |
| MPV / libmpv | Permitted, but ADR 0003 **keeps GStreamer**; the rationale there was never only licensing |
| `gst-plugins-ugly` / `bad` | **Permitted on licence grounds** — see § 4 on patents, which is a separate question |
| Locked/signed device image | Moot — no devices are distributed |

The LGPL relinking and replaceability rules in ADR 0004 § 3 also become moot for AQENO's own
distribution, because AQENO distributes source, not devices. They would return immediately if anyone
ever shipped hardware.

### 4. Patents remain a separate question, but a much smaller one

Patent exposure is not a copyright-licensing matter and is not resolved by GPLv3. However, under a
non-commercial posture distributing source code, the practical exposure for AAC and similar codecs
is far lower — German patent law exempts acts in the private, non-commercial sphere (§ 11 PatG), and
AQENO ships no decoder binaries.

Therefore **AAC / M4A / M4B support is permitted**, which closes the audiobook-format gap that
ADR 0003 identified as a real product cost. `.m4b` is a common audiobook container and excluding it
was the most damaging of the four constraints.

This is a judgement about proportionate risk, not a legal clearance.

### 5. Documentation and positioning rules

These are cheap, and they protect the posture:

- **AQENO is not marketed as a toy** and carries no age rating downward. The documented intended use
  is a *family audio device, set up and configured by adults*. A device marketed for children under
  14 may fall under the Toy Safety Directive 2009/48/EC and EN 71 — a regime this project must stay
  out of.
- **No safety claims anywhere.** Never "safe for children", "child-proof", "tested", "certified", or
  any implication of conformity assessment.
- **Build instructions carry an explicit build-at-your-own-risk notice**, and `SHOPPING_LIST.md` is
  documented as a description of what the maintainer used, not a recommendation or a bill of
  materials for a product.
- **Only CE-marked power supplies are referenced.** No specific battery or power-bank product is
  recommended; requirements are stated instead.
- **NFC tokens:** state minimum safe dimensions rather than suggesting small ones. Small parts are a
  choking hazard and tokens are central to the concept.
- **Licence compliance is still AQENO's own liability** and does not vanish with non-commerciality.
  Every dependency's licence stays recorded and CI-checked, per ADR 0004 § 2, which remains in force
  as an engineering practice.

### 6. Volume limiting is a safety feature, not a comfort setting

This follows directly from the posture and deserves its own point, because it is the one place where
AQENO's *own code* is the plausible path to personal injury.

The realistic harm from a children's audio device is **hearing damage**, and volume behaviour is
entirely AQENO's design — not a component manufacturer's. Under gross-negligence exposure, knowingly
shipping unlimited output for a child profile is precisely the wrong shape of risk.

Therefore:

- an absolute output ceiling applies to child profiles and cannot be raised from a child-facing
  surface;
- the night ceiling from `PRODUCT_FOUNDATION.md` § 6 is a hard limit, not a suggestion;
- headphone output is treated as a distinct, lower-limited path where it can be detected;
- defaults are conservative, and the limits are documented for the person setting the device up;
- the limits are covered by tests, in the same class as the dark-room invariant.

The concrete numeric values are gap G05, and this ADR promotes them from "missing detail" to
**prerequisite for the audio step of the first vertical slice**.

### 7. Exit optionality is preserved deliberately

Non-commercial operation does not mean the project has no future value. A later **sale of the
project, or employment by a manufacturer, remains open** — and unlike ongoing revenue, neither
conflicts with § 1, because selling intellectual property or taking a salary does not place a product
on the market.

Publishing under GPLv3 does not prevent this. **A copyright holder is not bound by the licence they
grant to others**, so AQENO's owner may relicense the work proprietary, dual-license it, or sell the
copyright outright — exactly the mechanism Qt and MySQL used.

That ability survives only if copyright stays consolidated. The following rules are therefore in
force from now, and they are cheap only if applied *before* the situation arises:

- **Every external contribution requires a signed contributor agreement** granting AQENO's owner the
  right to relicense, or an outright copyright assignment. Without it, the contributor retains
  copyright on their part and the whole work becomes impossible to relicense. **A single accepted
  contribution without this is effectively irreversible**, because it means finding and obtaining
  agreement from that person years later.
- **No anonymous or pseudonymous contributions** are accepted into the codebase.
- **Provenance is tracked.** This is an explicitly AI-assisted project, and the copyright status of
  AI-generated code is unsettled — under German law a work requires human creativity (§ 2 UrhG), so
  substantially AI-generated code may not be protected at all. That cuts both ways: it cannot be
  cleanly owned or sold, and it is a finding any acquirer's due diligence will surface. Commit
  authorship and co-authorship trailers are the provenance record; they are kept honest for that
  reason, not as etiquette.
- **The `AQENO` trademark should be registered** (DPMA or EUIPO). Trademarks are untouched by GPLv3,
  so the mark is the one asset that stays exclusively the owner's regardless of how widely the code
  is copied. It is also the cheapest action available and the one most likely to be regretted if
  skipped.
- **Enclosure designs may warrant registered-design protection**, on the same reasoning.
- **The specifications in this repository are themselves assets.** The product foundation, display
  behaviour contract, journeys and platform contracts are copyrightable works, and in a pre-MVP
  project they are plausibly worth more than the code.

**One tension must be named:** an acquisition contract will require representations and warranties —
typically that the seller owns the IP and that it infringes no third-party rights. That is
contractual liability, and it is the one place where "no liability" and "being bought" genuinely
collide. It can be capped and carved out, but not reduced to zero. The provenance rules above are
what make such warranties signable at all.

## Alternatives considered

**Non-commercial but with donations.** Marginally more sustainable and common practice for projects
of this kind. Rejected under this posture: it introduces exactly the commercial-activity ambiguity
the decision is meant to eliminate, for money the project has not asked for.

**Commercial and open (GPLv3, revenue from hardware and B2B).** The option recommended before this
requirement was stated, and still the strongest position if the goal were a product. Rejected because
it requires accepting liability, incorporating a limited-liability company, and carrying CE/GPSR
compliance — all of which the stated requirement excludes.

**Keep ADR 0004's optionality.** Rejected: it pays four concrete MVP costs to preserve a path now
deliberately closed.

**Publish nothing at all.** The only posture with genuinely zero exposure, since instruction
liability under § 823 BGB survives publication. Rejected as defeating the project's purpose; § 5
reduces this residual risk instead of eliminating it.

## Consequences

**Easier.** The licence question closes. ADR 0004's constraints lift, recovering AAC/M4B support and
removing custom on-screen-keyboard work from the MVP. GDPR falls out of scope entirely, because
without a hosted service AQENO is not a controller — which also removes the DPIA question, Art. 8
child-consent handling, and any processing agreement. Gap G23 is resolved rather than merely
documented. Several roadmap items disappear, which is a real reduction in scope.

**Harder.** The project is unfunded. Hardware, displays, boards and time are paid personally with no
route to recovery, and there is no mechanism to fund a second prototype revision or to compensate
contributors. If it later becomes untenable, the way out is ADR-driven and non-trivial: it means
incorporating and accepting compliance, not quietly selling a few kits.

The exception is § 7: employment by, or sale to, a manufacturer stays available and is the
liability-optimal way to be paid for this work, since an employer bears product liability for what it
places on the market, not the employee. Contributor-agreement and provenance discipline is the price
of keeping that door open, and it must be paid from the first external contribution onward.

**Constrained.** No sales of any kind, ever, without superseding this ADR *first*. Positioning
language in every public document is now load-bearing. Volume limiting is a safety requirement with
tests, not a feature.

**Residual risk that survives this decision.** Stated so it is not mistaken for zero:

1. **Intent** can never be excluded, and **gross negligence** remains under § 521 BGB by analogy.
   Practical rule: known safety defects get fixed and disclosed, never hidden.
2. **Instruction liability** for published build guides, enclosure designs and component lists
   (§ 823 BGB). Mitigated by § 5, not removed.
3. **Licence and copyright compliance** in AQENO's own dependencies and contributions.
4. **Trademark:** not registering "AQENO" lowers exposure but leaves the name available to others.
5. Anyone who builds AQENO and passes it to third parties becomes a manufacturer themselves —
   their exposure, unless they trade on AQENO's name.

## Documents to change on acceptance

This ADR is Proposed. On acceptance, and not before:

1. add a `LICENSE` file containing GPL-3.0 — this is the act that makes the licence real;
2. add SPDX headers (`GPL-3.0-or-later`) to source files as they are created;
3. `AGENTS.md` § "Dependency policy" — replace "compatible license for potential commercial
   distribution" with GPLv3 compatibility, and add the positioning rules from § 5 as binding;
4. `PRODUCT_FOUNDATION.md` § 15 — rewrite: optional cloud services no longer finance anything, and
   the deferred licensing decision is now made;
5. `ROADMAP.md` P5 — remove "Commercial hardware BOM study", "Optional remote-management/cloud
   business case" and the licensing decision; keep the DIY BOM, enclosure, security and privacy
   reviews;
6. `ARCHITECTURE.md` § "Decision still open" — remove "final open-source license";
7. `SHOPPING_LIST.md` and `docs/hardware/HARDWARE_REFERENCE.md` — add the § 5 notices;
8. `README.md` — state the licence and the non-commercial, no-safety-claims positioning;
9. mark ADR 0004 as Superseded, retaining it for its Qt/GStreamer module facts and its five named
   legal uncertainties, which remain valid reference material;
10. add the § 7 contribution rules to `AGENTS.md` and `ONBOARDING.md` — contributor agreement
    required, no anonymous contributions, provenance trailers kept honest — since these bind AI
    assistants as much as human contributors;
11. add a `CONTRIBUTING.md` with the contributor agreement, **before** the repository is made public.
    Making the repository public without it is the one step in this list that cannot be undone.
