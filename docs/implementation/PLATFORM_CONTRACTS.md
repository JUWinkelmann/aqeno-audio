# AQENO Platform Contracts

## Physical controls and input events

Concrete hardware first emits a normalized `ControlInput(logical_control, event)` through
`PhysicalInputSource`. Stable RH1 logical controls are `primary_left`, `primary_encoder` and
`primary_right`; they are not NeoKey channels, I2C addresses or GPIO pins. `navigation_encoder` is
the fourth defined logical control (ADR 0024 § 4). No RH1 adapter reports it today, so its mappings
exist and are unavailable — the same honest state as any other absent hardware. Available controls and
events come from the source's capabilities rather than being assumed by the Administration.

Buttons expose `short_press` and `long_press`. A rotary control may additionally expose
`rotate_left` and `rotate_right`; illumination is a separate capability. The one current long-press
threshold is 800 ms. A release produces either short or long, never both.

The device-wide `MappedInputBus` resolves those physical events through the controlled AQENO action
registry, locally and without HTTP/network involvement. Defaults are:

| Logical event | AQENO action |
|---|---|
| `primary_left.short_press` | `playback.previous` |
| `primary_encoder.rotate_left` / `rotate_right` | `volume.down` / `volume.up` |
| `primary_encoder.short_press` | `playback.play_pause` |
| `primary_right.short_press` | `playback.next` |
| `navigation_encoder.rotate_left` / `rotate_right` | `navigation.focus_previous` / `focus_next` |
| `navigation_encoder.short_press` | `navigation.select` |
| every current long press | unassigned |

`primary_left` and `primary_right` are the LEFT and RIGHT controls: **back and forward**, resolved by
content context (ADR 0024 § A3). In the current slice the only context is linear playback, so their
defaults remain `playback.previous` and `playback.next`. The navigation resolution arrives with the
first content-browsing level; nothing here is rebound in anticipation.

No default binds a long press, and no everyday action may require one (ADR 0024 § A2). Long press
remains available to adapters and to the registry for setup, service and hardware cases.
`display.wake` is bindable to a short press only.

Navigation actions (`navigation.focus_previous`, `navigation.focus_next`, `navigation.select`,
`navigation.back`) are ordinary entries in the controlled action registry and may be bound to any
control a source reports, including a spare button. **Volume and playback actions must not be
rebound to navigation on the same control that carries volume**: the product rule is that a volume
control stays a volume control (ADR 0024 § 2). The registry does not enforce that — it is a
Management-UI and review responsibility, because forbidding a mapping mechanically would also
forbid legitimate hardware AQENO does not know about yet.

Allowed actions are fixed product actions, never shell commands, URLs, scripts or arbitrary API
calls. Mappings are persistent device settings, not profile settings. Missing hardware leaves a
mapping intact and unavailable; unknown actions restored from a newer version remain unsupported
and are never silently remapped. A reset restores only these mappings and illumination preference.

After mapping, Application listeners receive the existing semantic events:

- `VolumeDelta(delta)`
- `TogglePlayback`
- `Next`
- `Previous`
- `WakeRequest`
- `FocusPrevious`, `FocusNext`, `Select`, `Back` — navigation, deliberately named apart from
  transport `Previous`/`Next` so no reader or mapping confuses the two
- `NfcPresented(tag_id)`
- `NfcRemoved(tag_id)` where supported

Navigation events are routed through the display service, which owns the wake decision and consumes
the input that woke the panel (`DISPLAY_STATE_MACHINE.md` Group G, note 15) before the Device UI
sees it. Transport and NFC keep their existing route and never wake anything.

**Wake behaviour is a property of the resolved action, not of the control** (ADR 0024 § A4). A
control whose meaning depends on context — LEFT and RIGHT — therefore carries the display semantics
of whatever it resolved to, and that resolution happens in the mapping layer before the display
service sees an event. Volume and Play/Pause are deliberately excluded from Group G: a first volume
step must reach audio in a dark room rather than being spent on lighting the panel.

No application code should depend on GPIO pin numbers.

Delivery at both boundaries follows ADR 0011: synchronous registration-order delivery, without
replay or coalescing. The fixed Previous → Encoder → Next ownership-confirmation sequence observes
logical RH1 short presses before configurable action mapping, so a custom mapping cannot disable
local Administration setup or recovery.

## Display contract

**Amended 2026-08-18 by ADR 0016.** The adapter receives panel power and a resolved brightness, not a
logical display state — otherwise every adapter would carry its own copy of profile-dependent
brightness policy. LEDs are a separate port driven by the same policy, because on Reference Hardware 1
they are separate devices on a separate bus.

Adapter capabilities:
- set panel power on/off;
- set brightness 0–100 where supported;
- report touch events, delivered to the display service rather than to the UI;
- report whether the panel has touch at all. Touch is an optional capability: a panel without it is
  fully supported, and a panel with it never makes touch a required path (ADR 0024 § 1);
- report whether it can achieve **authoritative off** — no intended visible output — rather than only
  zero backlight;
- user-facing LEDs through the LED contract below, under the same visual policy.

The display state machine (`DISPLAY_STATE_MACHINE.md`) resolves state and guards to that power and
brightness. Nothing outside `adapters/` sets either directly.

## LED contract
User-facing LEDs are semantic indicators, not hard-coded GPIO effects.

Required operations:
- set brightness 0–100%;
- true OFF;

Current Manager preferences are `off`, `subtle` and `clear`. Product/display policy resolves these
to brightness; concrete RGB colour remains the AQENO design policy inside the adapter, not a raw
user setting. A later temporary product-status cue may override the preference only while active
and must then return to it; no current feature needs such a cue.

Night/Dark-Room policy has authority to force all user-facing LEDs OFF.

## Audio contract
- load resolved source;
- play/pause/stop;
- seek where supported;
- next/previous context handled above engine layer;
- volume;
- state/error callbacks;
- no UI-specific behaviour.

The platform chooses a stable Linux audio device name. AQENO never relies on a numeric ALSA card
index and Core never names the MiniAmp or any other concrete output.

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
