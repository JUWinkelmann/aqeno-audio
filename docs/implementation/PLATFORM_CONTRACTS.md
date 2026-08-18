# AQENO Platform Contracts

## Input events
Hardware and simulators emit the same semantic events:

- `VolumeDelta(delta)`
- `TogglePlayback`
- `Next`
- `Previous`
- `WakeRequest`
- `NfcPresented(tag_id)`
- `NfcRemoved(tag_id)` where supported

No application code should depend on GPIO pin numbers.

Delivery follows ADR 0011: synchronous registration-order delivery, without replay or coalescing.

## Display contract

**Amended 2026-08-18 by ADR 0016.** The adapter receives panel power and a resolved brightness, not a
logical display state — otherwise every adapter would carry its own copy of profile-dependent
brightness policy. LEDs are a separate port driven by the same policy, because on Reference Hardware 1
they are separate devices on a separate bus.

Adapter capabilities:
- set panel power on/off;
- set brightness 0–100 where supported;
- report touch events, delivered to the display service rather than to the UI;
- report whether it can achieve **authoritative off** — no intended visible output — rather than only
  zero backlight;
- user-facing LEDs through the LED contract below, under the same visual policy.

The display state machine (`DISPLAY_STATE_MACHINE.md`) resolves state and guards to that power and
brightness. Nothing outside `adapters/` sets either directly.

## LED contract
User-facing LEDs are semantic indicators, not hard-coded GPIO effects.

Required operations:
- set brightness 0–100%;
- set logical colour where RGB is available;
- true OFF;
- optional pulse/fade only when policy permits.

Night/Dark-Room policy has authority to force all user-facing LEDs OFF.

## Audio contract
- load resolved source;
- play/pause/stop;
- seek where supported;
- next/previous context handled above engine layer;
- volume;
- state/error callbacks;
- no UI-specific behaviour.

## Persistence contract
Atomic persistence for:
- profiles/policies;
- content library;
- tag mappings;
- playback/resume;
- profile favorites, content audiences, collection inheritance and explicit access exceptions;
- settings.

Library queries accept an optional profile context and evaluate effective access in the persistence
adapter. Clients and the Device UI must not reconstruct or filter access rules item by item.

Unexpected power loss must not corrupt the library.

## Readiness states
1. BOOTING
2. LOCAL_READY
3. PLAYBACK_READY
4. UI_READY
5. NETWORK_READY
6. OPTIONAL_SERVICES_READY

Later states may not unnecessarily block earlier local functions. Entry criteria, what may fail
without stopping the ladder, and the capability/minimum-state table that makes "unnecessarily"
testable are specified in `docs/implementation/READINESS_STATES.md`.

## Reference performance targets
- wake input response: <500 ms target;
- display interactive after wake: <=1 s;
- warm application resume: <=2 s;
- cold boot to basic physical control readiness: <=8 s;
- cold boot to interactive home UI: <=10 s.
