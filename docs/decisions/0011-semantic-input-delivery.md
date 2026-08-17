# ADR 0011 — Semantic input delivery

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17
**Closes:** gap G06

## Context

Physical controls and the desktop keyboard must reach the application through the same semantic
events. `PLATFORM_CONTRACTS.md` already defines those events and `DEVELOPMENT.md` fixes the desktop
key mapping, but neither document says how an input adapter delivers an event.

The first slice is single-process (ADR 0002). It needs predictable control handling, including one
volume step per encoder detent, but it does not need persistence, replay, IPC or a general event
broker.

## Decision

An input adapter exposes an `InputBus` port. Application listeners register before the adapter is
started, and each input is delivered synchronously to every listener in registration order.

- Events are not retained or replayed. Input received before listeners are registered is ignored.
- Every event is delivered separately. In particular, adjacent `VolumeDelta` events are not
  coalesced.
- A listener failure propagates to the adapter boundary. The bus does not hide a partially handled
  control action and does not continue with later listeners after the failure.
- The bus is process-local. It has no serialization format and no network or socket transport.

The keyboard simulator implements the same port. Its `n` key remains a simulator control for
toggling the test environment's night guard; it is not promoted to a hardware input event.

## Consequences

Input handling is deterministic and directly testable. Slow listeners also delay later listeners,
so application handlers must remain short; background work belongs behind those handlers when it
is actually introduced.

There is deliberately no queue, subscriber priority, event history or asynchronous dispatcher.
Those mechanisms would add failure and shutdown semantics that the current product does not need.
