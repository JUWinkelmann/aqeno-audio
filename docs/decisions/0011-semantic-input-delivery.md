# ADR 0011 — Semantic input delivery

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17
**Closes:** gap G06

## Context

Physical controls and the desktop keyboard must reach the application through the same semantic
events. Configurable controls additionally require a stable hardware-independent event below that
semantic action: the Adafruit adapter must not know that a press means Play/Pause, while the
Application must not know that a logical encoder came from a seesaw board.

The first slice is single-process (ADR 0002). It needs predictable control handling, including one
volume step per encoder detent, but it does not need persistence, replay, IPC or a general event
broker.

## Decision

Hardware adapters expose `PhysicalInputSource`, which delivers a stable logical control plus gesture.
The device-wide mapping layer turns the controlled action ID into the existing semantic `InputBus`.
Keyboard simulation may emit `InputBus` events directly. Application listeners register before an
adapter is started, and each event at either boundary is delivered synchronously to every listener
in registration order.

- Events are not retained or replayed. Input received before listeners are registered is ignored.
- Every event is delivered separately. In particular, adjacent `VolumeDelta` events are not
  coalesced.
- A listener failure propagates to the adapter boundary. The bus does not hide a partially handled
  control action and does not continue with later listeners after the failure.
- The bus is process-local. It has no serialization format and no network or socket transport.

The keyboard simulator implements the same port. Its `n` key remains a simulator control for
toggling the test environment's night guard; it is not promoted to a hardware input event.

Mapping persistence stores logical control/event/action IDs, never board identity. The allowed
action registry is compiled AQENO product behaviour, not a macro facility. Administration ownership
confirmation observes the stable three RH1 short presses before the configurable mapping so setup
and password recovery cannot be remapped away.

## Consequences

Input handling is deterministic and directly testable. Slow listeners also delay later listeners,
so application handlers must remain short; background work belongs behind those handlers when it
is actually introduced.

There is deliberately no queue, subscriber priority, event history, arbitrary command registry or
asynchronous dispatcher.
Those mechanisms would add failure and shutdown semantics that the current product does not need.
