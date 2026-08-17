# ADR 0001 — Implementation language and runtime

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

`docs/implementation/FIRST_VERTICAL_SLICE.md` is the declared implementation target, but no
language or runtime has been chosen. `ARCHITECTURE.md` lists this as an open decision and
`AGENTS.md` forbids deciding it implicitly through a first commit. Nothing can be delegated or
tested until it is fixed.

Constraints that actually bear on the choice:

- The target is a Raspberry Pi 4B running Linux, with a 7-inch touch display.
- Control hardware is I2C (STEMMA QT rotary encoder, NeoKey 1x4) per
  `docs/hardware/HARDWARE_REFERENCE.md`. The mature, pre-existing driver ecosystem for these
  specific boards is Python (Adafruit CircuitPython/Blinka).
- `PLATFORM_CONTRACTS.md` sets cold boot to interactive home UI ≤ 10 s and to basic physical
  control readiness ≤ 8 s. This is the one target that pressures against a slow-starting runtime.
- `AGENTS.md` requires boring, readable technology and hardware-agnostic domain logic.
- This is an explicitly AI-assisted project, and part of the implementation work is intended to be
  delegated to weaker models. Language choice materially changes how well that works.

## Decision

**Python for the application core, adapters and UI layer.** Minimum supported version **3.11**
(Raspberry Pi OS Bookworm), developed and tested against **3.13** (Raspberry Pi OS Trixie).

Layering follows `ARCHITECTURE.md` as ordinary Python packages with no framework in the domain:

- `domain/` and `application/` — standard library only. No Qt, no GStreamer, no I2C, no `RPi.*`,
  no `board`/`busio` imports. This is enforced by an import-boundary test, not by convention.
- `adapters/` — the only place hardware and framework dependencies may appear.

Type hints are mandatory in `domain/` and `application/` and checked in CI.

## Alternatives considered

**Rust.** Best cold-boot time, strongest robustness guarantees, no GC pauses, and it would make
the ≤ 8 s target comfortable rather than tight. Rejected for now because it is markedly slower to
build in a discovery-phase project, the Adafruit I2C board ecosystem would have to be reimplemented
against raw I2C, and it is the worst of the candidates for delegating implementation to weaker
models — which is an explicit working constraint here, not a preference.

**C++ (with Qt directly).** Fastest startup and the most direct path to Qt, but the same delegation
problem as Rust plus a much higher defect surface for a small team. The project's stated preference
for boring and readable technology argues against it.

**Node.js / TypeScript.** Good UI story and good delegation properties, but the I2C hardware
ecosystem for these specific boards is weaker, and the realistic UI path is a browser surface,
which ADR 0002 rejects for separate reasons.

**Go.** Good startup and deployment story, weak GUI ecosystem on embedded Linux, weak I2C board
support for the chosen hardware.

## Consequences

**Easier.** Hardware bring-up for the chosen I2C boards is largely off-the-shelf. Domain logic is
fast to write and fast to test. Weaker models can be given a signature list and produce usable
domain code. One language spans domain, adapters and UI, so there is no cross-language boundary to
maintain inside the device.

**Harder.** Cold-boot time becomes a real engineering concern rather than a free property: Python
interpreter start plus Qt and GStreamer imports can plausibly consume a large share of the 10 s
budget. This is accepted deliberately because `ARCHITECTURE.md` already mandates staged readiness —
physical controls and local playback must become available before the full UI. The budget must be
measured early, not at the end.

**Constrained.** Import discipline becomes a load-bearing rule. Python makes it trivially easy to
import a hardware module into domain code and destroy the portability the whole architecture exists
to protect. Hence the import-boundary test as a first-class test, present from the first commit of
the slice.

**Open verification (P2 feasibility spike).** Measure on Reference hardware: interpreter plus
adapter import time; time to first semantic input handled; time to first audio. If controls are not
demonstrably usable within ~8 s under staged readiness, this ADR is revisited rather than the target
being quietly relaxed.
