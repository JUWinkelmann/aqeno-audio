# ADR 0016 — Display power authority and where display policy runs

**Status:** Accepted
**Date:** 2026-08-18
**Accepted:** 2026-08-18

## Context

`DISPLAY_STATE_MACHINE.md` is complete and implemented in `domain/display.py`: five states, the full
transition table, guards, and a `DisplayTransition` that already carries `consume_touch` and
`defer_until_ready`. Nothing imports it. There is no display port, no service driving it, and no
timer that ever fires `InactivityElapsed`.

Slice step 8 closes that gap, and three questions have to be answered before code exists, because
each one is expensive to reverse:

1. What does the port carry — a logical display state, or panel power and brightness?
2. Who owns the user-facing LEDs?
3. A wake touch must be consumed (invariant 7). Where does that happen, given that the UI runs
   in-process (ADR 0002) and would otherwise receive the touch first?

The requirement that shapes all three is the one ADR 0002 was chosen for: **the application owns the
display's power state**, and `OFF` must mean no intended visible output while audio continues.

## Decision

### 1. The port carries panel power and brightness, not display state

```
DisplayPanel:
    set_power(on: bool) -> None
    set_brightness(level: int) -> None      # 0–100, logical
    on_touch(listener) -> None
    capabilities() -> PanelCapabilities     # authoritative_off, brightness_control, touch
```

`PLATFORM_CONTRACTS.md` § Display contract lists "set logical state: OFF / DIM / INTERACTIVE /
AMBIENT / SETUP" among the adapter capabilities. **That wording is amended by this ADR**: an adapter
that receives `DIM` would have to know what dim means for the active profile, which is a
`CONFIGURATION_DEFAULTS.md` value and a policy decision. Two adapters would then hold two copies of
the same policy, and they would drift.

The state machine already resolves state plus guards to a brightness (`DISPLAY_STATE_MACHINE.md`
§ Brightness). The adapter receives the result. This keeps `AGENTS.md`'s rule — adapters emit and
apply, they never decide — and it is what makes the state machine testable without a panel.

**`authoritative_off` is a reported capability, not an assumption.** Whether the panel can really be
powered down depends on the display server, which is gap G24 and undecided. An adapter that can only
set brightness to zero says so, and the log says so once at startup. A backlight at zero on a panel
that still scans is not `OFF` in the sense `PRODUCT_FOUNDATION.md` § 6 requires, and the difference
must be visible rather than assumed away.

### 2. LEDs are a separate port under the same policy

```
StatusLeds:
    set_brightness(level: int) -> None      # 0–100; 0 is true off
```

Separate port because the hardware is separate — on Reference Hardware 1 the LEDs live on the encoder
and the NeoKey, not on the panel. Same policy because `DisplayPolicy.led_brightness` and note 12 of
the state machine make it one decision: `night_active` forces every user-facing LED to true off, and
so does `OFF`.

No colour and no pulse in this port today. `PLATFORM_CONTRACTS.md` § LED contract lists both, and
they are legitimate later; nothing in the current slice sets a colour, and an unused parameter would
be a speculative extension point.

### 3. The display service sits in front of the UI for touch

Touch arrives from the panel adapter at the **display service**, not at the UI. The service resolves
the transition and then either forwards the touch to its UI listener or swallows it.

This is the only placement that satisfies invariant 7 without the UI having to know about display
state. The alternative — the UI receives every touch and asks the display service whether it may act
— puts a policy check into every touch handler in QML, and one forgotten check is a child triggering
an action on a panel they cannot see. Making it structurally impossible is worth one indirection.

### 4. The service owns the timers, the readiness ladder gates the wake

`application/display.py` holds the current state, assembles `DisplayGuards` at each transition, drives
`InactivityElapsed`, `DimElapsed` and `SetupIdleElapsed` through the injected `Clock`, and applies the
resulting power and brightness.

A `WakeRequest` before `UI_READY` sets a single pending-wake flag, applied when the ladder reaches
`UI_READY` (`READINESS_STATES.md` § 4). One flag, not a queue: three impatient presses during boot
mean one wake. This requires `application/readiness.py`, which is specified but not built, so it is
part of this step.

## Alternatives considered

**A logical-state port.** Matches the platform contract's current wording and makes the adapter's job
sound simpler. Rejected in § 1: it pushes profile-dependent brightness policy into every adapter.

**One port for panel and LEDs.** Fewer files, and they are driven by the same policy. Rejected because
they are different devices on different buses, and a panel adapter that must also speak I²C to a
NeoKey is exactly the coupling ADR 0010 § 2 forbids.

**Brightness zero as `OFF`.** Simpler, works everywhere, no capability reporting. Rejected because it
silently redefines the product's central requirement. A panel that is scanning at zero backlight still
emits light in a dark room, and the maintainer would discover this at a child's bedside rather than in
a log line.

**Let the UI own the display state**, since it is in-process anyway. Rejected: display state must
survive a UI that has not started or has crashed, and `READINESS_STATES.md` requires playback and
transport to work with no `UI_READY` at all. Display policy is application state that the UI observes.

## Consequences

**Easier.** The dark-room requirement becomes testable without hardware: a fake panel records power
and brightness calls, and the state machine's ten invariants become assertions over that recording.
`OFF` while audio continues is then a scenario test rather than a hope.

**Harder.** Three concurrent sources now touch the display service — input events, playback state
changes and timers — so the service needs the same deliberate thread discipline `PlaybackSession`
already has. Timer cancellation on every state change is the part most likely to leak a stale
callback.

**Constrained.** `PLATFORM_CONTRACTS.md` § Display contract is amended per § 1. Nothing outside
`adapters/` may set panel power or brightness. The UI receives touches from the display service, not
from the panel adapter, and may not subscribe to the adapter directly.

**Open.** G24 remains: whether `eglfs` or a Wayland compositor gives us authoritative panel power is
unanswered, and this ADR deliberately makes that answer *observable* rather than deciding it. The real
panel adapter is not finished until it reports `authoritative_off` truthfully on Reference Hardware 1.
