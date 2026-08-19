# AQENO Platform Contracts

## Physical controls and input events

Concrete hardware first emits a normalized `ControlInput(logical_control, event)` through
`PhysicalInputSource`. The five logical controls are `select_encoder`, `previous`, `next`,
`volume_encoder` and `home` (ADR 0026 § 2). They are named for their permanent role, never for a
NeoKey channel, I2C address, GPIO pin or enclosure position, and each means one thing in every
state. RH1 reports four of them; no RH1 adapter reports `select_encoder`, so its mappings exist and
are unavailable — the same honest state as any other absent hardware. Available controls and events
come from the source's capabilities rather than being assumed by the Administration.

Buttons expose `short_press` and `long_press`. A rotary control may additionally expose
`rotate_left` and `rotate_right`; illumination is a separate capability. The one current long-press
threshold is 800 ms. A release produces either short or long, never both.

The device-wide `MappedInputBus` resolves those physical events through the controlled AQENO action
registry, locally and without HTTP/network involvement. Defaults are:

| Logical event | AQENO action |
|---|---|
| `select_encoder.rotate_left` / `rotate_right` | `navigation.focus_previous` / `focus_next` |
| `select_encoder.short_press` | `navigation.select` |
| `previous.short_press` | `playback.previous` |
| `next.short_press` | `playback.next` |
| `volume_encoder.rotate_left` / `rotate_right` | `volume.down` / `volume.up` |
| `volume_encoder.short_press` | `playback.play_pause` |
| `home.short_press` | `navigation.home` |
| every current long press | unassigned |

`previous` and `next` are content order, never UI navigation: they move within the active content as
ADR 0009 § 2 defines per kind, and they never move focus. This replaces ADR 0024's context-resolved
LEFT/RIGHT, which could not be operated without looking because the person could not know which
context they were in. `home` is the always-available way out and is not rebindable in practice —
binding another action onto it, or `navigation.home` onto another control, defeats the one control
whose purpose is being predictable (ADR 0026 § 4).

No default binds a long press, and no everyday action may require one (ADR 0024 § A2). Long press
remains available to adapters and to the registry for setup, service and hardware cases.
`display.wake` is bindable to a short press only.

Navigation actions (`navigation.focus_previous`, `navigation.focus_next`, `navigation.select`,
`navigation.home`) are ordinary entries in the controlled action registry and may be bound to any
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
- `FocusPrevious`, `FocusNext`, `Select`, `Home` — navigation, deliberately named apart from
  transport `Previous`/`Next` so no reader or mapping confuses the two. There is no `Back` event,
  because there is no back control (ADR 0026 § 4)
- `NfcPresented(tag_id)`
- `NfcRemoved(tag_id)` where supported

Navigation events are routed through the display service, which owns the wake decision and consumes
the input that woke the panel (`DISPLAY_STATE_MACHINE.md` Group G, note 15) before the Device UI
sees it. Transport and NFC keep their existing route and never wake anything.

**Wake behaviour is a property of the control** (ADR 0026 § 5). ADR 0024 § A4 had to make it a
property of the resolved action, because LEFT and RIGHT changed roles; with permanent roles that
indirection is withdrawn. `select_encoder` and `home` wake; `previous`, `next` and `volume_encoder`
never do. **`home` is executed on the press that woke the panel rather than consumed** (note 17):
consumption protects against an unseen context-dependent action, and HOME has none. Volume and
Play/Pause stay outside Group G entirely — a first volume step must reach audio in a dark room
rather than being spent on lighting the panel.

No application code should depend on GPIO pin numbers.

Delivery at both boundaries follows ADR 0011: synchronous registration-order delivery, without
replay or coalescing. The fixed PREVIOUS → VOLUME → NEXT ownership-confirmation sequence observes
those three permanent control identities before configurable action mapping, so a custom mapping
cannot disable local Administration setup or recovery. Because the identities are permanent
(ADR 0026 § 2), the sequence carries to target hardware unchanged.

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

Control illumination is **contextual guidance, never permanent status display, and never a
precondition for operating a control** (ADR 0026 § 1.7, § 9). Every control must be findable and
usable with all light off.

Night/Dark-Room policy has authority to force all user-facing LEDs OFF, and does so today without
exception. ADR 0026 § 9 names that behaviour the `off` night illumination policy — the only one that
exists, the default, and not configurable. The `on_approach` and `subtle` values are recorded
vocabulary for a deliberate future human choice and require proximity hardware AQENO does not have. **DARK means zero visible light** — no display,
no control LED, no status LED, no glowing HOME key, no unavoidable operating indicator. No hardware
may force visible residual light.

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
