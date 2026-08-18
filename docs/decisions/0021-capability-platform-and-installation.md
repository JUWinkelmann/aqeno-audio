# ADR 0021 — Capability-oriented platform and installation boundary

**Status:** Accepted
**Date:** 2026-08-18

## Context

ADR 0010 already keeps board libraries out of Core, while the deployment prototype assumes a mutable
checkout at `/opt/aqeno` on Raspberry Pi. AQENO needs one supported reference installation today
without making Raspberry Pi, its image or its boot configuration the product architecture.

## Decision

Raspberry Pi 4B running a pinned Raspberry Pi OS Lite 64-bit release is **AQENO Reference Platform
1**, and is the only supported appliance platform for now. Desktop Linux remains a development
target. Other boards are neither implemented nor advertised.

Runtime composition is capability-oriented and continues to use the existing ports for audio,
display, input, LEDs and NFC. Platform integration owns OS packages, display/audio setup, buses,
device permissions, mount/service configuration and hardware detection. Domain/Application never
branch on board marketing names. No generic HAL or speculative adapters are introduced.

AQENO is packaged as a wheel with bundled UI assets in immutable, versioned releases below
`/opt/aqeno/releases`; an atomic `current` link activates a validated release. System-integrated Qt
and PyGObject may remain platform packages. Containers are rejected for Reference Platform 1 because
their device/lifecycle cost solves no current isolation need.

An installer applies the generic AQENO release through supported platform provisioning. A platform
image combines a pinned OS with the same primitives; it is a convenience artifact, not AQENO itself.
The installer is idempotent, dry-run capable, validates existing Data and never partitions or formats
implicitly. AQENO runs unprivileged. Future privileged operations use a fixed, narrow helper rather
than root API execution or constructed shell commands.

Recovery and A/B SYSTEM partitions are deferred. Versioned application rollback plus external SYSTEM
repair and portable Data backup address current risks with less machinery.

The detailed normative contract is `docs/implementation/PLATFORM_INSTALL_CONTRACT.md`.

## Consequences

- Supporting another board requires a tested platform manifest/adapter but not Core forks.
- Release rollback is possible without making user state part of a release.
- The reference installer/service may implement bounded slices of this contract, but remain
  bootstrap tooling until platform detection, dry-run/phase recovery and RH1 validation are complete.
- Exact Pi package/display decisions are pinned and validated in the Reference Platform manifest;
  they are not scattered across application modules.
- An image may be platform-specific while backups and AQENO application data remain portable.

## Alternatives considered

A Pi-specific application tree was rejected because it makes later support a fork. A universal
abstract HAL was rejected because existing ports already express current needs. Containers were
rejected for current resource and hardware-access cost. Maintaining a golden SD card was rejected as
non-reproducible. Building recovery and A/B slots now was deferred because their maintenance and
update surface exceeds the failure risk they currently remove.
