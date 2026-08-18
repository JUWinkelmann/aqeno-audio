# Display State Machine

**Date:** 2026-08-17
**Amended:** 2026-08-18 by ADR 0024 — Group G, physical navigation
**Closes:** gap G04
**Authority:** implements `docs/product/DISPLAY_BEHAVIOR.md`. Where this document and the prose
conflict, the prose is the product intent and this document is the defect.

This is the normative transition table. `DISPLAY_BEHAVIOR.md` describes the intent; that description
is not implementable without the table below, because prose leaves each reader to invent the cases it
does not mention.

## States

`OFF` · `DIM` · `INTERACTIVE` · `AMBIENT` · `SETUP`, as defined in `DISPLAY_BEHAVIOR.md`.

Initial state on boot is **`OFF`**. The machine may not enter `INTERACTIVE`, `DIM`, `AMBIENT` or
`SETUP` before readiness state `UI_READY` (`READINESS_STATES.md`). Nothing renders before that rung,
so any of those states would mean a lit panel with nothing on it.

Two different outcomes, deliberately:

- A `WakeRequest`, `TouchOnPanel` or Group G navigation input arriving earlier is **queued, not
  discarded**, and applied when
  `UI_READY` is reached — one pending wake, however many times it is requested.
- `AmbientRequested`, `AmbientScheduleStart` and `SetupRequested` are **blocked** with reason
  `ui_not_ready`, not queued. Setup is adult-initiated and retried in a second; an Ambient schedule
  that opened during boot should not spring on later out of order.

*`SETUP` was added to this rule on 2026-08-18, together with the guard in `domain/display.py`, after
the display service made the gap visible.*

## Guards

Referenced by name in the table. All are read at transition time, never cached.

| Guard | Meaning |
|---|---|
| `ui_ready` | Readiness state has reached `UI_READY` |
| `night_active` | A Night/Dark-Room policy or scene is active |
| `playback_active` | Audio is playing or paused with a live session |
| `ambient_enabled` | Ambient is switched on for the active profile |
| `ambient_authorised` | The role model permits the current actor to run Ambient |
| `profile_allows_dim` | Active profile permits a glanceable `DIM` stage during playback |
| `setup_authorised` | Actor holds Manager or Owner rights |

## Events

**Group A — explicit visual requests.** `WakeRequest`, `TouchOnPanel`, `SetupRequested`,
`SetupCompleted`, `AmbientRequested`, `AmbientExited`, `ContentSelected`

**Group B — physical transport.** `VolumeDelta`, `TogglePlayback`, `Next`, `Previous`

**Group C — NFC.** `NfcPresented`, `NfcRemoved`

**Group D — playback and system.** `PlaybackStarted`, `PlaybackStopped`, `PlaybackPaused`,
`TrackChanged`, `BufferingStarted`, `BufferingEnded`, `MetadataUpdated`, `PlaybackError`,
`NetworkChanged`, `ServiceReady`, `VolumeChanged`

**Group E — timers.** `InactivityElapsed`, `DimElapsed`, `SetupIdleElapsed`, `AmbientScheduleStart`,
`AmbientScheduleEnd`

**Group F — policy.** `NightActivated`, `NightDeactivated`

**Group G — physical navigation.** `Navigate` — one resolved navigation action: focus movement,
activation of the focused item, or back. ADR 0024 makes navigation physical, and physical navigation
is the replacement for the panel touch it must not require. It therefore takes touch's display
semantics, not the transport rule.

Membership is decided by the **resolved AQENO action, not by the button** (ADR 0024 § A4). A control
whose meaning depends on context — LEFT and RIGHT are back and forward — belongs to Group G only in
the moments it resolves to navigation, and to Group B whenever it resolves to transport. Volume and
Play/Pause never join Group G: consuming a first volume step to light a dark panel would remove the
one guarantee the dark room exists for.

## Transition table

`—` means **no transition and no timer reset**: the event is handled elsewhere in the application and
the display is not involved. This is a decision, not an omission.

| Event | from `OFF` | from `DIM` | from `INTERACTIVE` | from `AMBIENT` | from `SETUP` |
|---|---|---|---|---|---|
| `WakeRequest` | → `INTERACTIVE` ¹ | → `INTERACTIVE` | reset timer | → `INTERACTIVE` | reset timer |
| `TouchOnPanel` | → `INTERACTIVE` ¹ ² | → `INTERACTIVE` ² | reset timer ³ | → `INTERACTIVE` ² | reset timer ³ |
| **Group G** `Navigate` | → `INTERACTIVE` ¹ ¹⁵ | → `INTERACTIVE` ¹⁵ | reset timer ¹⁶ | → `INTERACTIVE` ¹⁵ | reset timer ¹⁶ |
| `ContentSelected` | n/a | n/a | reset timer | n/a | reset timer |
| `AmbientRequested` | → `AMBIENT` ⁴ | → `AMBIENT` ⁴ | → `AMBIENT` ⁴ | reset schedule | — |
| `AmbientExited` | — | — | — | → `INTERACTIVE` | — |
| `SetupRequested` | → `SETUP` ⁵ | → `SETUP` ⁵ | → `SETUP` ⁵ | → `SETUP` ⁵ | reset timer |
| `SetupCompleted` | — | — | — | — | → `INTERACTIVE` |
| **Group B** (all) | **stay `OFF`** ⁶ | **stay `DIM`** ⁶ | **no timer reset** ⁶ | **stay `AMBIENT`** ⁶ | **no timer reset** ⁶ |
| `NfcPresented` | **stay `OFF`** ⁷ | stay `DIM` ⁷ | no timer reset ⁷ | stay `AMBIENT` ⁷ | reset timer ⁸ |
| `NfcRemoved` | stay `OFF` | stay `DIM` | no timer reset | stay `AMBIENT` | reset timer ⁸ |
| **Group D** (all) | **—** | **—** | **—** | **—** | **—** |
| `InactivityElapsed` | n/a | → `OFF` | → `DIM` if `profile_allows_dim && playback_active && !night_active`, else → `OFF` | — ⁹ | n/a |
| `DimElapsed` | n/a | → `OFF` | n/a | n/a | n/a |
| `SetupIdleElapsed` | n/a | n/a | n/a | n/a | → `OFF` ¹⁰ |
| `AmbientScheduleStart` | → `AMBIENT` ⁴ | → `AMBIENT` ⁴ | — ¹¹ | — | — |
| `AmbientScheduleEnd` | — | — | — | → `OFF` | — |
| `NightActivated` | stay `OFF` ¹² | → `OFF` | → `OFF` | → `OFF` | stay `SETUP` ¹³ |
| `NightDeactivated` | **stay `OFF`** ¹⁴ | — | — | — | — |

### Notes

1. Only if `ui_ready`. Otherwise the request is queued and applied at `UI_READY`.
2. **The touch that wakes is consumed.** It must not be delivered to whatever UI element lies beneath
   the finger. A child tapping a dark panel must never trigger an action they cannot see. This is a
   hard requirement, not a refinement.
3. The touch is delivered to the UI normally.
4. Requires `ui_ready && ambient_enabled && ambient_authorised && !night_active && !playback_active`.
   If any guard fails, there is no transition and the reason is logged. Ambient is never an automatic fallback for
   inactivity — the only paths into `AMBIENT` are an explicit request or a configured schedule.
5. Requires `ui_ready && setup_authorised`. Otherwise no transition.
6. **Volume, play/pause, next and previous never change display state and never reset the visual
   inactivity timer.** The timer measures *visual* interaction. This is the dark-room requirement in
   its most literal form: the child turns the volume down at 3 a.m. and the room stays dark. It is
   also why the timer is not reset — a physical action is not a request to keep the screen on.
7. **NFC does not wake the display.** Presenting a token is a physical action, in the same class as a
   button. A figure placed on the device at bedtime must not light the room. Open for user testing:
   whether an *unassigned* tag should produce brief visual feedback, which would need a `DIM` path
   that Kids profiles do not currently have.
8. In `SETUP`, NFC events are delivered to the tag-assignment flow instead of launching content.
9. Inactivity does not apply in `AMBIENT`; it ends by schedule, by explicit exit, or by
   `NightActivated`.
10. `SETUP` times out to `OFF` so a forgotten configuration screen cannot light a bedroom all night.
    Setup progress is preserved, and re-entry resumes where it left off.
11. Ambient waits rather than interrupting an active user. It starts at the next opportunity, i.e.
    when `InactivityElapsed` reaches `OFF` and the schedule is still open.
12. Also forces every user-facing LED to true `OFF` and applies the night volume ceiling. See
    `PLATFORM_CONTRACTS.md` § LED contract.
13. An administrator mid-configuration is not interrupted, but brightness drops to the night minimum
    and `SetupIdleElapsed` shortens to the night value.
14. **Night ending never wakes the display.** Nothing in this machine transitions *out* of `OFF`
    automatically — every path out requires an explicit human request or an authorised Ambient
    schedule. A Group G navigation input is an explicit human request; a scheduled alarm would be a
    third class and needs its own amendment here before it exists (ADR 0025 § 3).
15. **The navigation input that wakes is consumed**, for the reason in note 2. Rotating a knob or
    pressing NAV in a dark room must not also move focus or start content the person cannot see.
    Wake first, act on the next input.
16. Delivered to the UI normally. In `SETUP` it belongs to the setup flow, like a touch.

## Wake target

On any transition into `INTERACTIVE` from `OFF`, `DIM` or `AMBIENT`:

- if `playback_active` → **Now Playing**, showing the current item's artwork;
- otherwise → **Home**.

Rationale: `DISPLAY_BEHAVIOR.md` asks for "the least distracting relevant view". During playback the
relevant view is what is playing, not a grid of alternatives inviting a new choice. This answers one
of that document's open questions and should be confirmed in user testing.

## Brightness

`DIM` is a deliberately reduced presentation, not the `INTERACTIVE` view with brightness lowered.
The presentation layer removes visible controls, navigation and unnecessary detail. Glanceable is
the UX name for this use of `DIM`, not another machine state.

| State | Normal | `night_active` |
|---|---|---|
| `OFF` | panel off, no output | panel off, no output, **all user-facing LEDs off** |
| `DIM` | profile dim level | night minimum |
| `INTERACTIVE` | profile interactive level | night minimum |
| `AMBIENT` | profile ambient level | unreachable |
| `SETUP` | profile interactive level | night minimum |

Concrete values are in `CONFIGURATION_DEFAULTS.md`.

## Invariants

Each of these is a test, not a guideline. They are the invariants `AGENTS.md` requires protected.

1. **No transition in this table pauses, stops, seeks or alters playback.** A screen timeout must
   never touch audio.
2. **No Group D event produces any transition.** Buffering, chapter change, metadata arrival, stream
   errors and background service readiness are invisible.
3. **Group B events behave identically in all five states**, and are fully functional in `OFF`.
   Group G is deliberately *not* Group B: navigation is the one input class whose entire purpose is
   looking at something.
4. **No automatic transition leaves `OFF`.** Only an explicit human request or an authorised Ambient
   schedule does.
5. **Entering `OFF` produces no flash, fade-up or farewell animation.**
6. **Leaving `OFF` shows no partially painted frame.** The first visible frame is complete.
7. **A wake touch is consumed** and never activates an underlying control. The same holds for a
   waking navigation input (note 15).
8. **`night_active` forces every user-facing LED to true off**, and `AMBIENT` is unreachable while it
   holds.
9. **`OFF` means no intended visible output**, per `PLATFORM_CONTRACTS.md`.
10. The machine is **deterministic**: for a given state, event and guard set there is exactly one
    outcome, and every cell above is defined.

## Deliberately out of scope

Whether `NfcRemoved` stops playback is a domain question, not a display question, and belongs with
gap G21. Nothing here depends on the answer.
