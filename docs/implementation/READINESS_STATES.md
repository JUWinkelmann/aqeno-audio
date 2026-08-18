# Readiness States

**Date:** 2026-08-18
**Closes:** gap G13
**Authority:** implements `PLATFORM_CONTRACTS.md` § Readiness states and `PRODUCT_FOUNDATION.md` § 12
(startup, wake and perceived readiness). Where this document and those conflict, they are the intent
and this document is the defect.

`PLATFORM_CONTRACTS.md` names six states and one rule: *"later states may not unnecessarily block
earlier local functions."* That rule is the product requirement — an appliance that plays a bedtime
story must not wait for a network it does not need — and the word **unnecessarily** is not testable.
This document replaces it with a dependency table that is.

## 1. The ladder is monotonic

Readiness only ever advances. A state, once reached, is never revoked.

This is a decision, not an observation. The alternative — falling back to an earlier state when
something breaks — would force every consumer to handle oscillation, and it conflates two different
questions. *Readiness* says what has become available since power-on. *Degradation* (§ 6) says what is
currently impaired. An audio device unplugged mid-story is a `DEVICE` failure
(`FAILURE_STATES.md` row 10); it does not un-ready playback, and the resume position, the library and
the buttons all still mean what they meant a second earlier.

States are reached in order. A state whose entry criteria fail is simply never reached, and the ladder
stops there — later rungs do not become reachable by skipping it.

## 2. The states

### BOOTING

**Reached:** at process start.
**Guarantees:** nothing. Display is `OFF` — the initial state of the display machine, which may not
leave it before `UI_READY` (`DISPLAY_STATE_MACHINE.md`).

Work in this state: resolve paths and environment overrides, start logging, read and validate
`settings.toml`.

| May fail without stopping the ladder | Effect |
|---|---|
| Settings file missing, malformed or out of range | defaults are used, rejected keys logged, the file is not rewritten (ADR 0007 § 1); degraded flag `settings_invalid` |

### LOCAL_READY

**Reached when** the domain database is open, migrated to the current schema, and the active profile
is resolved.
**Guarantees:** the library, tag mappings, resume positions and profile are readable. Everything the
device knows about itself is available.

| May fail without stopping the ladder | Effect |
|---|---|
| Filesystem read-only or full | opened read-only; playback and reads work, writes do not; degraded flag `storage_unwritable` (ADR 0007 § 6) |
| A library root is missing | that root is skipped by the scan (`CONTENT_INGESTION.md` § 1) |

| Stops the ladder | Effect |
|---|---|
| Database corrupt or unopenable | `database_corrupt`. **The process stays up.** No further state is reached; the surface stays dark and a Manager decides on repair. Never an automatic wipe (`FAILURE_STATES.md` row 13). |
| Database schema newer than the code | same, reported distinctly. Downgrading silently is worse than failing (ADR 0007 § 5). |

**AQENO never exits on a failure a Manager could repair.** Exiting turns a repairable device into a
dead box, and there is no console on it.

### PLAYBACK_READY

**Reached when** the audio engine is constructed and reports a usable output device, **and** every
application listener is registered on the `InputBus`, **and** the input adapters have been started —
in that order.

**Guarantees:** physical transport works. Content can be selected, launched, resumed and controlled.
This is the rung `PRODUCT_FOUNDATION.md` § 12 calls *basic physical control readiness*, and it is what
makes the device usable in the dark with no screen at all.

The ordering is load-bearing. ADR 0011 does not retain or replay input: an event arriving before its
listeners exist is ignored, permanently. So adapters start last, and this state is not reached until
they have. There is no queue to drain and no startup race to reason about.

| May fail without stopping the ladder | Effect |
|---|---|
| No audio output device | `audio_device_missing`. The ladder continues — the UI, the library and the display all still work; nothing plays. A device whose speaker died still shows a child their tiles. |

### UI_READY

**Reached when** the view layer is loaded, the first frame can be rendered, and the display adapter
holds authority over panel power.

**Guarantees:** the display machine may leave `OFF`. Any `WakeRequest` pending from § 4 is applied now.

| May fail without stopping the ladder | Effect |
|---|---|
| UI fails to load or crashes | `UI_READY` is never reached; the panel stays `OFF`. **Playback and physical controls continue to work.** |

That last row is the audio-first principle made mechanical rather than aspirational: AQENO with a dead
UI is a working audio player, not a brick. It is a named test, not a hope.

### NETWORK_READY

**Reached when** an interface has a usable route. Nothing more is checked — no reachability probe, no
captive-portal detection, no DNS test.

**Guarantees:** an HTTP Source may be *attempted*. It guarantees nothing about whether it will work;
a stream that fails is `stream_unreachable`, an ordinary content failure.

**This state is never awaited.** No local capability observes it, no startup step blocks on it, and
there is no timeout after which anything is retried at startup. On a device that is offline forever,
the ladder stops here permanently and nothing about the product changes. ADR 0010 § 1 requires the
Core to be *fully functional* with no network — not to degrade gracefully — and never waiting is what
that means at startup.

### OPTIONAL_SERVICES_READY

**Reached** immediately after `NETWORK_READY`, because nothing registers here.

There is no service layer, no API, no account and no telemetry (ADR 0010 § 3). The rung exists so the
ladder matches the platform contract and so a future service has a defined place to announce itself.
Nothing may depend on it, and adding something that does is a product decision requiring an ADR.

## 3. The dependency table

This replaces "unnecessarily". Every capability declares the **lowest** state at which it must work.
A capability may not observe, await or be gated by any state above its own row.

| Capability | Minimum state |
|---|---|
| Read settings and profile | `LOCAL_READY` |
| Browse the library; see tiles as data | `LOCAL_READY` |
| Content scan / ingestion (ADR 0014 § 5) | `LOCAL_READY` |
| Play, pause, stop local content | `PLAYBACK_READY` |
| Volume, `Next`, `Previous` from physical or simulated controls | `PLAYBACK_READY` |
| Resume a position; persist a position | `PLAYBACK_READY` |
| Launch content by NFC tag | `PLAYBACK_READY` |
| Sleep timer, night policy, volume ceilings | `PLAYBACK_READY` |
| Display leaving `OFF`; any visible surface | `UI_READY` |
| Playing an HTTP Source or radio | `NETWORK_READY` |
| *(nothing)* | `OPTIONAL_SERVICES_READY` |

The mechanical form of the rule: **for each row, the capability must work in a process where no higher
state is ever reached.** That is directly executable — construct the process, stop the ladder at the
declared state, exercise the capability.

## 4. Input before PLAYBACK_READY

G13's specific question, and the one place where two documents look contradictory.

- The **`InputBus` does not queue.** Input arriving before listeners are registered is ignored and
  never replayed (ADR 0011). Since adapters start only once listeners exist (§ 2), this window is
  closed by construction rather than handled.
- The **display policy does queue one wake.** `DISPLAY_STATE_MACHINE.md` requires a `WakeRequest`
  arriving before `UI_READY` to be held and applied on arrival.

Both are true because they describe different components. The queue lives in the display policy — a
registered listener holding a single pending-wake flag — not in the bus. The flag is a boolean, not a
backlog: three impatient presses during boot produce one wake, which is what the person pressing
meant.

A button pressed while the panel is still dark and playback is already possible does what it always
does. Transport does not wait for a screen.

## 5. What is shown during startup

**Nothing.** No splash screen, no logo, no progress bar, no spinner, no "starting up" text.

The display is `OFF` until `UI_READY` and then shows the actual surface — populated, or the calm empty
state when the library is empty (`FAILURE_STATES.md` row 11). An appliance does not narrate its own
boot, a progress indicator in a dark bedroom is light nobody asked for (`PRODUCT_FOUNDATION.md` § 6),
and a spinner would make a fast startup *feel* slower by drawing attention to it.

If the ladder stops before `UI_READY`, the panel stays dark. The child experiences a device that does
not respond; the Manager finds the reason in the log and, later, in the management surface. That is the
same calm-failure shape as everywhere else in `FAILURE_STATES.md`.

## 6. Degradation is a second axis

Readiness answers *what is available*. Degraded flags answer *what is impaired*. They are orthogonal
and must not be collapsed into one enum — a device can be fully `OPTIONAL_SERVICES_READY` and unable to
persist a single byte.

Current flags, each mapping to an existing failure code: `settings_invalid`, `storage_unwritable`,
`database_corrupt`, `audio_device_missing`.

A flag is set once and cleared only when its condition is re-tested — never on a timer. Flags are
Manager-facing and never child-facing.

## 7. Timing targets, made measurable

`PLATFORM_CONTRACTS.md` § Reference performance targets become instrumentable once the rungs are
named. Measured on Reference Hardware, from power-on unless stated:

| Target | Measured to |
|---|---|
| cold boot to basic physical control readiness ≤ 8 s | `PLAYBACK_READY` |
| cold boot to interactive home UI ≤ 10 s | `UI_READY` |
| warm application resume ≤ 2 s | `PLAYBACK_READY`, process start to rung |
| wake input response < 500 ms | not a readiness measurement — input to audible effect, `UI_READY` already held |
| display interactive after wake ≤ 1 s | not a readiness measurement — wake event to first frame |

The last two are **wake**, not boot. Waking a display does not move the ladder: readiness never
regresses (§ 1), and a warm device that has been idle for hours is still `OPTIONAL_SERVICES_READY`.

Each rung logs its arrival with a monotonic timestamp taken from the injected `Clock`, which is what
the roadmap's startup-instrumentation track needs and costs one log line per state.

## 8. Where this lives in code

`application/readiness.py`: an ordered enum, the current rung, and registration for observers that
need to act on arrival — the display policy's pending wake, the ingestion scan. `__main__.py` advances
it, because the composition root is the only place that knows which adapters exist.

No new port. Readiness is a fact the application computes about itself, not a capability an adapter
provides.

## 9. Invariants worth a named test

1. The ladder never moves backwards, including when an adapter fails after its rung was reached.
2. Every capability in § 3 works in a process where no higher state is reached — one test per row.
3. Local playback works with no network at all, and nothing at startup waits on `NETWORK_READY`.
4. A failing UI leaves playback and physical transport fully working.
5. A missing audio device does not stop the ladder, and the library remains browsable.
6. A corrupt database stops the ladder at `BOOTING`, keeps the process alive, and deletes nothing.
7. Input adapters are started only after listeners are registered, so no event is delivered to an
   empty bus.
8. A `WakeRequest` before `UI_READY` produces exactly one wake at `UI_READY`; three produce one.
9. Nothing is displayed before `UI_READY` in any state, including failure states.
10. Each rung is logged once, with a monotonic timestamp, in order.

## 10. Deliberately not decided here

The Management API attaches after `PLAYBACK_READY` and remains optional degradation (ADR 0018);
suspend/resume of the whole device as distinct from display wake; and the shutdown sequence, which is
`PlaybackSession.shutdown()` plus an orderly close and needs no ladder of its own.
