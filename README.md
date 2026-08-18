# AQENO Player

AQENO is an **open, adaptive, audio-first player platform** designed to combine extremely simple interaction with freedom of content and hardware.

The first focus is **AQENO Kids**; the same core is intended to support **AQENO Easy**.

## Current status

**First Vertical Slice implemented on desktop; Reference Hardware validation is in progress.** The
domain, persistence, GStreamer audio, semantic input, process composition, bounded Kids Early Device
UI, display policy and end-to-end scenarios exist. The RH1 encoder/NeoKey adapter is implemented but
still needs verification on the assembled prototype; panel, final audio and other physical boundaries
must not be claimed complete before on-device evidence exists.
The implementation target is
[`docs/implementation/FIRST_VERTICAL_SLICE.md`](docs/implementation/FIRST_VERTICAL_SLICE.md).

On the reference device, local administration opens at **http://aqeno.local**. No IP address or
port is part of the normal product journey; direct loopback/IP access is development and recovery
only.

AQENO is a personal project. Licensing, publication and commercialisation are deferred by intent —
see [`ADR 0006`](docs/decisions/0006-non-commercial-posture.md).

## Start here

1. [`ONBOARDING.md`](ONBOARDING.md) — start here, especially for AI assistants.
2. [`PRODUCT_FOUNDATION.md`](PRODUCT_FOUNDATION.md) — what AQENO is and the product rules.
3. [`AGENTS.md`](AGENTS.md) — mandatory instructions for AI coding agents and vibe-coding workflow.
4. [`ARCHITECTURE.md`](ARCHITECTURE.md) — architectural guardrails and open decisions.
5. [`ROADMAP.md`](ROADMAP.md) — discovery-to-MVP progression.
6. [`DEVELOPMENT.md`](DEVELOPMENT.md) — toolchain, repository layout, how to run and test.
7. [`docs/DOCUMENTATION_GAPS.md`](docs/DOCUMENTATION_GAPS.md) — what is not yet decided.
8. [`docs/product/COMPETITIVE_REVIEW.md`](docs/product/COMPETITIVE_REVIEW.md) — what other products do well; a benchmark, not a scope authority.
9. [`MISTAKES.md`](MISTAKES.md) — mistakes already made; do not repeat them.
10. [`docs/decisions/`](docs/decisions/) — durable architecture/product decisions.

## Core idea

> **AQENO adapts to people — people should not have to adapt to the player.**

Fundamental playback is physical and screen-independent. The screen appears when it adds value. AQENO remains local-first, supports open content and should run on a defined range of freely selectable hardware.
