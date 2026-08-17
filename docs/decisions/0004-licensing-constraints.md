# ADR 0004 — Dependency licensing constraints and deferred project licence

**Status:** Proposed — **ON HOLD**
**Date:** 2026-08-17

> **On hold as of 2026-08-17.** AQENO is a personal project built for the maintainer's son. Nothing is
> distributed, published or sold, so the licence question is not live and the constraints below do not
> bind. See ADR 0006 for the reasoning and for what survives the deferral.
>
> **The restrictions in § 5 do not apply** while nothing is distributed — AAC/M4B, Qt Virtual
> Keyboard and the fuller GStreamer plugin sets are available. ADRs 0002 and 0003 keep PySide6 and
> GStreamer on technical merit, not on licence grounds.
>
> Retained as reference material that stays valid: the Qt/GStreamer module facts (§ 5), the LGPL
> compliance rules (§ 3, which return the moment anyone distributes hardware), and the five named
> legal uncertainties at the end.
>
> **Later product decision:** ADR 0012 excludes Qt Virtual Keyboard regardless of this ADR's on-hold
> status and does not replace it with a custom keyboard.

> **This is engineering risk management, not legal advice.** It records the constraints AQENO will
> work under so that decisions stay reversible. Before any public release under a chosen licence, and
> before any commercial distribution, the specific obligations below require review by someone
> qualified to give legal advice. Named uncertainties are listed at the end and must not be treated
> as settled.

## Context

`PRODUCT_FOUNDATION.md` § 15 defers the open-source/commercial licensing decision and requires that
the architecture "must not accidentally foreclose either path". `AGENTS.md` requires every dependency
to have "a compatible license for potential commercial distribution".

That check is currently impossible to perform: compatibility is only definable against a target, and
no target exists. This is gap G18, and it has stopped being theoretical — ADR 0002 and ADR 0003 both
need the rule *now*, because the licence constraint is what decides PySide6 over PyQt6 and GStreamer
over MPV.

The decision that matters is therefore not "which licence does AQENO ship under" — that can still
wait — but **"which future licensing paths are we paying to keep open, and at what price"**.

## Decision

### 1. The project licence stays deferred; the constraint does not

AQENO's own licence remains an explicit future decision. Until it is made, all work proceeds under
one binding interim constraint:

> **Keep the proprietary-commercial distribution path open.** No code under GPL (any version) may be
> linked into, or combined into a single work with, the AQENO application.

This is the strictest credible target, so anything built under it remains compatible with every
later choice — permissive, LGPL, GPL or commercial. Reversing the constraint later is cheap;
retrofitting it is not.

### 2. Dependency licence rules

| Licence | Status |
|---|---|
| Public domain / MIT / BSD / ISC / Apache-2.0 | **Preferred.** No further review. |
| LGPLv2.1 / LGPLv3 | **Permitted** subject to the compliance rules in § 3. |
| MPL-2.0 | **Permitted** (file-level copyleft; keep modifications in their own files). |
| GPL / AGPL (any version) | **Not permitted** for anything linked or combined with the application. |
| Commercial / proprietary | **Requires an ADR**, including cost and exit path. |
| Unknown / unstated | **Not permitted.** An unlicensed dependency is not usable. |

Every dependency's licence is recorded in the dependency manifest with its version, and the check
runs in CI. A dependency whose licence changes between versions is treated as a new decision.

### 3. LGPL compliance rules (binding on packaging)

Qt (ADR 0002) and GStreamer (ADR 0003) are the two LGPL components at AQENO's core. To rely on the
LGPL exception rather than the full copyleft:

- **Dynamic linking only.** No static linking of LGPL libraries into an AQENO binary.
- **No vendored, modified copies.** Use system or clearly versioned upstream builds. If an LGPL
  library must be patched, the patch and its source are published.
- **The library must be replaceable on the shipped device.** The user must be able to substitute
  their own build of Qt or GStreamer and have AQENO still run. This forbids a locked, signed or
  read-only-by-design device image — which is the single most important consequence of this ADR for
  any future commercial hardware.
- **Ship the licence texts**, the list of LGPL components and their versions, and either the library
  source or a valid written offer for it.
- **Document the relink path**, i.e. enough build information for the substitution above to be
  actually possible rather than nominally permitted.

### 4. Separate programs on the device are not a problem

Raspberry Pi OS, systemd, the kernel and ordinary userland are GPL, and AQENO running *on* them is
mere aggregation, not a combined work. This is the normal position of every Linux appliance.

But note: **distributing a ready-made SD-card image means distributing all of that GPL software**,
which carries its own source-offer obligations independent of AQENO's licence. That is a
distribution-mechanism decision, and it belongs in the packaging ADR.

### 5. Module and plugin restrictions that follow

- **Qt:** LGPLv3 modules only. Qt Charts, Qt Data Visualization and Qt Virtual Keyboard are
  understood to be GPLv3-or-commercial in Qt 6 and are excluded. ADR 0012 avoids complex on-device
  text entry; AQENO does not implement a replacement keyboard without a real product need.
- **PySide6, never PyQt6.** PyQt6 is GPLv3-or-commercial from Riverbank and would defeat § 1
  outright.
- **GStreamer:** `core`, `base` and `good` only. `ugly` and `bad` are excluded on licence and patent
  grounds.

### 6. Patent-encumbered codecs

Distinct from copyright licensing and not solved by it. MP3 (patents expired 2017), Vorbis, Opus,
FLAC and WAV are treated as safe. **AAC / M4A / M4B is not**, and this has a direct product cost
because `.m4b` is a common audiobook container — see ADR 0003 § Consequences. For the MVP, AAC is
unsupported and fails with a clear, calm message; the commercial position is resolved before
commercial distribution, not before the MVP.

## Alternatives considered

**Choose GPLv3 for AQENO now.** This deserves more weight than it might first appear, because it
fits AQENO's stated philosophy — open content, no lock-in, printable enclosures, bring your own
hardware. It would immediately remove most of the friction above: PyQt6, MPV and the fuller
GStreamer plugin sets all become available, the LGPL relinking analysis largely stops mattering, and
the on-screen keyboard could be Qt Virtual Keyboard instead of custom work. It does **not** prevent
selling hardware with AQENO on it. What it does foreclose is proprietary derivatives — including by
AQENO itself — and it imposes GPLv3's anti-tivoization requirements on shipped devices. Rejected for
*now* only because § 1 is reversible into this position at any time, whereas the reverse is not.

**Permissive-only (MIT/Apache) with no copyleft dependencies at all.** Maximum downstream freedom.
Rejected as unrealistic: it would exclude Qt and GStreamer simultaneously, leaving no credible UI or
audio stack for this hardware.

**Dual-licence AQENO (open plus commercial), like Qt itself.** A coherent long-term business model
and compatible with § 1. Rejected as premature: it requires contributor licence agreements from the
first external contribution onward, which is machinery this project does not need yet — but the
constraint in § 1 keeps it available.

**Defer entirely and decide nothing.** The status quo. Rejected because it blocks ADR 0002 and
ADR 0003 and makes `AGENTS.md`'s dependency policy unenforceable.

## Consequences

**Easier.** The dependency policy in `AGENTS.md` becomes mechanically checkable. Every later
licensing choice stays available. ADR 0002 and ADR 0003 are unblocked with a defensible rationale
rather than a preference.

**Harder — and this is the point to weigh.** Keeping the commercial-proprietary path open has a
measurable price, paid in the MVP:

- complex on-device text entry must be avoided or separately justified;
- MPV, a genuinely good fit for the audio port, is unavailable;
- AAC/M4B audiobook support is absent, in an audiobook-centric product;
- packaging must guarantee LGPL replaceability, which rules out a locked device image and adds real
  work before enclosure freeze.

**If the proprietary path is not actually wanted, all four costs disappear.** This is a product and
business question, not a technical one, and it is worth answering deliberately rather than by
default. Revisit this ADR before introducing any on-device free-text entry.

**Constrained.** No dependency enters the project without a recorded licence. Device images cannot be
locked down. Codec coverage is narrower than users will expect.

## Named uncertainties requiring legal review

These are flagged rather than answered, and no work should assume a particular resolution:

1. Whether LGPLv3 § 4 combined with GPLv3 § 6 "Installation Information" imposes obligations on
   AQENO as a *User Product* beyond the replaceability rules in § 3 above.
2. Per-module Qt 6 licensing must be verified against the exact Qt version used. Qt has moved modules
   between LGPL and GPL across releases; the § 5 list is current understanding, not a citation.
3. Per-plugin GStreamer licensing must be verified at the packaged versions, including whether
   distribution-provided `good` builds pull in anything from `ugly` or `bad`.
4. AAC patent status and licensing obligations vary by jurisdiction and by whether AQENO decodes,
   distributes or merely plays.
5. If The Qt Company's commercial licence is ever adopted, its terms may constrain prior or parallel
   LGPL use; this must be checked before, not after.
