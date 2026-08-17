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
Adapter capabilities:
- set logical state: OFF / DIM / INTERACTIVE / AMBIENT / SETUP;
- set brightness where supported;
- report touch/wake events;
- guarantee that OFF means no intended visible output;
- control associated user-facing LEDs through the same visual policy.

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
- settings.

Unexpected power loss must not corrupt the library.

## Readiness states
1. BOOTING
2. LOCAL_READY
3. PLAYBACK_READY
4. UI_READY
5. NETWORK_READY
6. OPTIONAL_SERVICES_READY

Later states may not unnecessarily block earlier local functions.

## Reference performance targets
- wake input response: <500 ms target;
- display interactive after wake: <=1 s;
- warm application resume: <=2 s;
- cold boot to basic physical control readiness: <=8 s;
- cold boot to interactive home UI: <=10 s.
