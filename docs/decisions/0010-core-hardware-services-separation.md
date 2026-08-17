# ADR 0010 — Core, hardware integration and optional services are separable

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

AQENO's current implementation targets a Raspberry Pi 4 with a specific set of I2C peripherals
(`docs/hardware/HARDWARE_REFERENCE.md`). That configuration is a **Reference Hardware
implementation**, not a permanent product requirement, and the project should not have to be rebuilt
if the hardware platform or the distribution model changes later.

Three futures should stay reachable without a rewrite, and none of them should be chosen now:

- AQENO runs on a different SBC, or on hardware built by someone else;
- AQENO's local core stays freely available while optional services exist above it;
- AQENO remains purely a personal project (ADR 0006 — the current situation).

This ADR is about **optionality, not anticipation**. It fixes a boundary, not a business model.

## Decision

> **AQENO separates local product logic, concrete hardware integration and optional external
> services, so that the hardware platform and any future distribution model remain exchangeable
> decisions.**

Three layers, with one rule each:

### 1. Core — local product logic

`domain/`, `application/`, `ports/` and `config/`. Everything needed for a self-sufficient local
AQENO: playback rules, library, tag logic, interaction, display logic, local configuration.

**Rule: the Core must remain fully functional with no network and no external service.** Not "should
degrade gracefully" — fully functional. `P03 Local first` is a product principle, and this ADR makes
it an architectural boundary.

### 2. Hardware integration — one implementation among several

`adapters/`. GPIO, I2C, NFC reader, display power, audio output, LEDs, buttons, rotary encoder,
power state.

**Rule: the Core carries no knowledge of any specific board, bus or pin.** The current Raspberry Pi
configuration is `AQENO Reference Hardware v0` — the first implementation of these ports, explicitly
not the only possible one. A second platform must be addable by writing adapters, without touching
`domain/` or `application/`.

### 3. Optional services — architecturally possible, deliberately absent

Remote management, synchronisation, backup, multi-device, fleet management, integrations.

**Rule: no function is routed through a server today because it might become a subscription
tomorrow.** Equally, nothing in the architecture *requires* that every future capability be local,
free or open — services may later sit above the Core, on the Core's terms.

**Nothing in this layer is implemented. There is no service layer, no API, no account, no licence
check, no telemetry, and none is to be added without a specific product decision.**

### 4. What makes the boundary hold

The boundary is enforced mechanically where that is cheap, because a documented rule that nothing
checks is a rule that erodes:

- the existing import-boundary test (ADR 0001, ADR 0008 § 6) extended to cover `config/`;
- a test that **no module outside `adapters/` imports networking** — this turns "no artificial SaaS
  dependency" from a promise into an invariant;
- a test that `application/` never imports `ui/`, and `ui/` never imports `adapters/`;
- hardware adapters named for the **technology they speak**, not the board they were first tested on:
  `adapters/input/i2c_seesaw.py`, not `adapters/input/pi.py`.

### 5. What this ADR explicitly does not decide

- whether AQENO is open source, proprietary, or dual-licensed — deferred by ADR 0006;
- whether any commercial service, certification programme or hardware business ever exists;
- whether AQENO is sold, given away, or kept private;
- which SBC is supported beyond the current Reference Hardware.

Anyone reading this ADR as evidence that a commercial direction was chosen has misread it.

## Alternatives considered

**Do nothing; the layering already exists.** Genuinely defensible: `ARCHITECTURE.md`, ADR 0001 and
`DEVELOPMENT.md` already describe these boundaries, and the import-boundary test already enforces
most of them. Rejected only because two things are missing that cost almost nothing — the network
check, and a written statement that the Pi is one implementation rather than the platform. Without
the latter, a future contributor reasonably reads `HARDWARE_REFERENCE.md` as "this is what AQENO
runs on".

**Introduce a capability/plugin framework now**, so alternative hardware is a first-class concept.
Rejected as premature: `AGENTS.md` forbids abstractions before a use case requires them, and there is
currently exactly one hardware target and zero hardware adapters. The `Capability` concept in
`DOMAIN_MODEL.md` should be implemented **with the first hardware adapter**, driven by a real second
case, not invented ahead of it.

**Introduce a local API or service boundary now**, so services can attach later. Rejected: it
contradicts ADR 0002's in-process decision, adds an authentication surface `AGENTS.md` warns about,
and builds infrastructure for a feature nobody has decided to have. The cheaper equivalent is the
rule that `ui/` calls `application/` services — a future API adapter can then wrap the same services
without a redesign.

**Restructure into separate packages or repositories per layer.** Rejected as disproportionate for a
project with no code in two of the three layers.

## Consequences

**Easier.** A second hardware platform becomes an adapter-writing exercise. Any future service can
attach above the Core without the Core having been shaped around it. The Pi's role is written down,
so it will not silently harden into a requirement.

**Harder.** Every hardware adapter now needs a port and a fake before it is useful, and its contract
suite runs against both (ADR 0008 § 3). This is real work per adapter, and it is the cost of hardware
independence being true rather than claimed.

**Constrained.** Nothing outside `adapters/` may open a socket. Hardware adapters are named for their
technology. The Core may not require a service to function — not now, and not once a service exists.

**Not constrained.** This ADR places no obligation on future functionality to be local, free or open.
That question is deliberately left where ADR 0006 left it.
