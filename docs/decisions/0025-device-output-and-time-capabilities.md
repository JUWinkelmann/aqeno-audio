# ADR 0025 — Device output direction and the time pillar

**Status:** Accepted
**Date:** 2026-08-18
**Relates to:** ADR 0016, ADR 0017, ADR 0023, ADR 0024

## Context

ADR 0023 makes time one of AQENO's three pillars, and ADR 0024 makes the display an assisting
surface rather than the primary control. Both change what the display is *for*, which invites two
hardware conclusions that must not be drawn silently: that AQENO depends on a particular panel
technology, and that a clock, timer or alarm can be built now.

RH1 uses a 7-inch 800 × 480 DSI panel whose display-server path is still unresolved (gap G24), and
carries semantic RGB LEDs on its Qwiic controls. The intended later hardware is smaller and has no
required touch. Nothing in the repository yet says which of those properties AQENO may rely on.

## Decision

### 1. Display class is a preference, never a dependency

The preferred later display is compact — roughly 4 to 5 inches — with high contrast, excellent black
level, good viewing angles, controllable brightness and, preferably, true pixel-off. AMOLED/OLED is
therefore preferred, because true black serves the existing product rule directly: **active when
useful, visually quiet when not.**

AMOLED is explicitly **not** an architectural dependency. AQENO must remain modellable with LCD/IPS,
OLED, AMOLED or no display at all (ADR 0017 § 1). Display technology lives in the platform/adapter
layer; Domain and Application know display *state*, never panel technology.

The 800 × 480 layout in `DEVICE_UI_BLUEPRINT.md` is consequently RH1's prototype layout. Encoder-
first information architecture is designed so a smaller panel with fewer simultaneous items remains
possible, and layouts are verified at the real viewport of whatever panel is being built for.

A good display can carry Now Playing, library navigation, artwork, clock, alarm, visual timer,
wake-up visualisation, a personal-message signal and status feedback. That is the justification for
investing in one panel instead of adding several single-purpose indicators — not a licence to keep
something on the screen.

### 2. No required status LED

A separate status or RGB LED is not part of the target hardware. The display carries status
feedback. No indicator is added merely because embedded devices traditionally have one.

RH1's existing NeoPixel/encoder illumination stays: it is prototype hardware, it is already behind
the `StatusLeds` port, and the port keeps a null implementation for hardware without lights
(`NullStatusLeds`). Nothing may assume user-facing light exists, and the Night/Dark-Room authority
over true off is unchanged. A dedicated LED returns only with a concrete use case, as an optional
capability.

### 3. Time capabilities: direction, not implementation

Clock, alarms, recurring alarms, audio alarm sources, alarm volume with gradual increase, sleep
timer and a visual timer are legitimate AQENO capabilities under the time pillar. **None is
implemented or scheduled by this ADR.** What is decided are the constraints any later implementation
inherits:

- **A visual timer presents remaining time graphically** — a total area or circle whose visible
  share decreases — so that a person who cannot read a numeric time still understands it. The
  general principle is used; no protected product design is copied.
- **Timer presets are administration.** Name, duration, optional artwork, optional completion sound
  and optional profile assignment are configured in the web client and reuse the existing profile
  and content-assignment mechanisms (ADR 0019). No new user, permission or assignment architecture
  is invented, and bulk assignment follows the rules already in place.
- **A timer may run alongside playback.** The UI must be able to show that a timer is active without
  permanently displacing Now Playing, and timer completion must resolve against audio deliberately —
  overlay, brief interruption or another defined signal — never as competing uncoordinated sources.
- **An alarm must not depend on the network.** A network-sourced alarm needs a local fallback, or it
  is not an alarm.
- **A scheduled alarm is the third path out of `OFF`.** `DISPLAY_STATE_MACHINE.md` invariant 4
  permits leaving `OFF` only through an explicit human request or an authorised Ambient schedule. An
  alarm — and any sunrise visualisation preceding it — is an authorised schedule of the same class
  and requires its own explicit amendment to that table when it is implemented. It must never arrive
  as an incidental side effect of a scheduler.
- **Night/Bedtime authority is not weakened.** Where the configured mode demands complete darkness,
  complete darkness wins: no permanent clock, no status LED, no glowing controls, no standby
  animation.

### 4. Wake-up light uses the display, honestly

A first sunrise function may use the display alone: dark → slowly increasing brightness → visual
sunrise → alarm audio. No additional RGB or wake-up-light hardware is planned for the first target
device.

A small panel is **not** a room wake-up light and must not be described as one. Real indirect
lighting may later be added as an optional hardware capability; the architecture must permit that
without presupposing it — which the existing `StatusLeds` and display ports already do.

## Alternatives considered

**Commit to AMOLED as the reference display.** Rejected: it would put a panel technology into the
product definition, and AQENO must survive its supply.

**Keep a status LED "for reliability".** Rejected: an indicator whose meaning the display already
carries is a second thing to design, dim, silence at night and repair.

**Implement clock and timer now, since the pillar is decided.** Rejected: ADR 0023 § 6 and the
project's scope rule. The current milestone is RH1 validation of the existing slice.

**Let an alarm reuse `AMBIENT`.** Rejected: `AMBIENT` means authorised passive content and would
lose its invariant. An alarm is its own authority with its own audio consequences.

## Consequences

- Display work is judged against a future smaller panel as well as RH1's, which keeps information
  density honest.
- Product documentation may describe AQENO as a modern radio alarm without any alarm code existing.
- The display-server question (G24) stays the gate for authoritative panel off, and a later AMOLED
  panel would raise it again for its own driver path.
- Any future alarm, timer or sunrise implementation starts with a display-state-machine amendment,
  not with a scheduler.

## Amendment — 2026-08-18: implementation order inside the time pillar

The time capabilities are not built in parallel. After RH1 validation, exactly one is completed end
to end first:

1. **Visual timer** — including its physical setup path and the graphical remaining-time model.
2. Only after its UX and hardware validation: clock, alarm, radio-alarm behaviour, sunrise.

The product vision in § 3 and § 4 is unchanged; only the order is constrained. The reason is
capacity, not doubt — a half-built clock plus a half-built timer is worth less than one finished
timer, and the timer is the capability whose interaction model the other three will reuse.
