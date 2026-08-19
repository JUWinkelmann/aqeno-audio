# Interaction Matrix

**Date:** 2026-08-19
**Authority:** implements ADR 0026. Where this table and the ADR conflict, the ADR is the product
intent and this document is the defect.
**Scope:** what each physical control does in each AQENO situation.

This is the normative counterpart to `DISPLAY_STATE_MACHINE.md`. That document owns display
transitions; this one owns control meaning. Its purpose is to **prove that five controls are
sufficient** — and to record honestly where they are not yet proven.

Situations marked **(future)** have no implementation and no device surface today. They are listed
because the control vocabulary must be shown to carry them before the capability is built; listing
one here authorises nothing.

## 1. Default rules

These hold in **every** situation. The tables below list only deviations; `·` means the default
applies unchanged.

| # | Default |
|---|---|
| D1 | **SELECT rotate** moves focus by one detent on a surface that offers a choice, and wraps. Where there is no choice, it does nothing. |
| D2 | **SELECT press** activates the focused element. Where nothing is focused, it does nothing. |
| D3 | **PREVIOUS / NEXT** move within the active content's order (ADR 0009 § 2). With no active playback they do nothing. They never move focus and never navigate. |
| D4 | **VOLUME rotate** changes volume by one step, in every state, bounded by the active ceiling. |
| D5 | **VOLUME press** toggles play/pause of the active session. With nothing loaded it does nothing. |
| D6 | **HOME** returns to Home. It never stops or pauses playback, and it always works. |
| D6a | **A transport or volume press never changes the visible surface.** Only Now Playing may be left because playback ended; browsing is unaffected (implemented and tested 2026-08-19). |
| D7 | **NFC presented** resolves a local assignment through the active profile's effective access. It never wakes the display. |
| D8 | **Touch**, where present, reaches the same application actions and is required for none of them. |
| D9 | **Display:** only SELECT and HOME wake a dark panel. SELECT's waking input is consumed; HOME's is executed (ADR 0026 § 4). PREVIOUS, NEXT, VOLUME and NFC never wake and never reset the visual timer. |
| D10 | **Control illumination** follows the night illumination policy (ADR 0026 § 9). Only `off` exists today, so control light is dark whenever Night is active. |
| D11 | **Audio feedback** is not emitted per keypress. The result of the action is the feedback (P20). |
| D12 | **Spoken feedback (future)** announces focus and state changes when explicitly enabled. It is not implemented and requires no microphone. |
| D13 | A control never becomes dangerous by context: no situation binds an unexpected destructive action to a control the person cannot see. |

## 2. Device states

| # | Situation | SELECT rotate | SELECT press | PREV / NEXT | VOL rotate | VOL press | HOME | Display |
|---|---|---|---|---|---|---|---|---|
| 1 | **Boot** | queued until `UI_READY` | queued | active as soon as `PLAYBACK_READY` | active from `PLAYBACK_READY` | active from `PLAYBACK_READY` | queued as one pending wake | stays `OFF` until `UI_READY` |
| 2 | **Active / Home** | moves between areas | opens the focused area | · (nothing playing → nothing) | · | · | already home; no change | `INTERACTIVE` |
| 3 | **Sleep** (display dark, device ready) | wakes, consumed | wakes, consumed | · acts silently | · acts silently | · acts silently | wakes **and** goes Home | `OFF` |
| 4 | **Wake** | first input consumed, second acts | as left | never woke anything | never woke anything | never woke anything | wakes and acts | → `INTERACTIVE`, target per `DISPLAY_STATE_MACHINE.md` |
| 5 | **Dark / Night** | wakes at night minimum brightness | as left | · fully operable in the dark | · | · | wakes, goes Home | `OFF`; LEDs per D10 |
| 33 | **Controlled shutdown** | — | — | — | — | — | — | **no control on the primary surface by design** (ADR 0026 § 8); see conflict C5 |
| 34 | **Restart after power loss** | · | · | · | · | · | · | resumes as `OFF`; resume position per `RESUME_BEHAVIOR.md` |

## 3. Content and playback

| # | Situation | SELECT rotate | SELECT press | PREV / NEXT | VOL rotate | VOL press | HOME |
|---|---|---|---|---|---|---|---|
| 2 | **Home** | moves between content areas, wrapping | opens the focused area — starts nothing | **nothing** | · | · | already home |
| 6 | **Browse** | moves focus between items, wrapping | starts the focused item | **nothing** — they are not navigation | · | · | back to Home |
| 7 | **Starting audio** | — | starts immediately; no confirmation step | — | · | · | returns Home; playback continues |
| 8 | **Music** | no choice on Now Playing → nothing | nothing | previous / next track | · | · | · |
| 9 | **Audio drama / audiobook** | nothing | nothing | previous / next chapter, else −30 s / +60 s | · | · | · |
| 10 | **Podcast** | nothing | nothing | previous / next chapter, else −30 s / +60 s | · | · | · |
| 11 | **Radio** | nothing | nothing | previous / next favourite where one exists, else ignored — see C4 | · | · | · |
| 12 | **Volume** | — | — | — | one step per detent, ceiling-bounded | — | — |
| 13 | **Pause / resume** | — | — | — | · | the single control for both | · |
| 14 | **Previous / Next** | — | — | per content kind, identical with the display off | — | — | — |
| 26 | **Display off during playback** | wakes, consumed | wakes, consumed | acts, display stays dark | acts, display stays dark | acts, display stays dark | wakes, goes Home, playback continues |

## 4. NFC

| # | Situation | Behaviour |
|---|---|---|
| 15 | **Token recognised** | Resolves the AQENO-local assignment and starts it. Does not wake the display. An unassigned token is calm and does nothing destructive. Recognition never authorises extraction from another content system (ADR 0013). |
| 16 | **Token removed** | Whether playback stops is a domain question, still open (gap G21). No control behaviour depends on the answer. |

All five controls keep their meaning while a token is present. A token is a shortcut, never a mode.

## 5. Time capabilities — **(future)**

Nothing below is implemented. ADR 0025's amendment fixes the order: visual timer first, end to end;
clock, alarm and sunrise only afterwards.

| # | Situation | SELECT rotate | SELECT press | PREV / NEXT | VOL rotate | VOL press | HOME |
|---|---|---|---|---|---|---|---|
| 17 | **Setting a timer** | changes the value | confirms and starts | nothing | · volume stays volume | · | leaves without starting |
| 18 | **Timer running** | normal navigation; the timer does not own the device | normal | normal transport | · | · | · |
| 19 | **Timer ends** (interruptive) | nothing | acknowledges and ends | nothing | · | · | ends it |
| 20 | **Setting an alarm** | changes the value | confirms | nothing | · | · | leaves without saving |
| 21 | **Alarm armed, waiting** | nothing special; no permanent surface | · | · | · | · | · |
| 22 | **Alarm ringing** (interruptive) | nothing | nothing | nothing | changes alarm volume | **snooze — see conflict C1** | ends the alarm |
| 23 | **Snooze active** | · | · | · | · | · | · |

Audio control stays independent while a timer runs: the timer does not take AQENO over. No snooze is
required for the timer. Under Night, no permanent timer illumination exists; at timer end the
relevant control may become briefly visible according to the illumination preference.

An alarm is the third path out of `OFF` and needs its own amendment to
`DISPLAY_STATE_MACHINE.md` before it exists (ADR 0025 § 3). It must never arrive as a scheduler side
effect.

## 6. Ambient, messages — **(future)**

| # | Situation | Behaviour |
|---|---|---|
| 24 | **Picture frame** (`AMBIENT`) | Explicitly enabled and authorised, never an idle fallback. PREVIOUS / NEXT step through images — see C3. HOME leaves `AMBIENT`. SELECT press does nothing unless the surface offers a choice. |
| 25 | **Send to AQENO / personal message** | Appears as **content**, not as a notification. No interruptive state, no badge, no counter, no attention mechanic (P12, P19). Reached and started like any other item: focus with SELECT, press to play — **never automatically** (ADR 0027 § 9). Playing it pauses media and resumes afterwards, because a message is content rather than a notification (§ 5). Arriving at night is completely silent. A delivered message is local and may be heard again. |

## 7. Sensing and environment

| # | Situation | Behaviour |
|---|---|---|
| 27 | **Hand approaches, lit room** | No illumination change. The controls are already visible; light added here would be decoration. |
| 28 | **Hand approaches, dark room** | **Today: nothing happens**, deliberately — no AQENO reports proximity and only the `off` policy exists. The intended `on_approach` behaviour is that the relevant controls fade up gently and return to full off after a short inactivity period. Proximity never triggers an action — it is illumination assistance only (ADR 0026 § 10). |
| 29 | **Proximity sensor unavailable** | Illumination falls back to its static policy. Every control remains fully operable. Nothing is presented as broken or missing. |
| 30 | **Ambient sensor unavailable** | Display and illumination use the profile's configured brightness. No adaptive behaviour, no error surface. |

## 8. Availability, failure and touch

| # | Situation | Behaviour |
|---|---|---|
| 31 | **Offline** | Local playback, all five controls, NFC and resume are unaffected. Network state is not shown in normal media views. |
| 32 | **Failure state** | Calm treatment inside the current surface, never a modal dead end and never technical language (`FAILURE_STATES.md`). It never wakes a dark display. **HOME always escapes it** — that is the control's core justification. |
| 35 | **Touch present** | Touch reaches the same application actions: tapping artwork equals focusing it with SELECT and pressing. A tap activates directly and does not first move focus. A waking touch is consumed. |
| 36 | **Touch absent or disabled** | Nothing is lost. Every path in this document is physical. RH1 must be validatable with touch deliberately ignored. |

## 9. Design conflicts found

Recorded rather than silently resolved, per ADR 0026 and `AGENTS.md`.

**C1 — Alarm snooze on the VOLUME press.** The proposal `VOLUME press = snooze` collides with the
permanent-meaning rule: VOLUME press is play/pause in every state. The plausible reading is that
they are the same action — *pause what is currently sounding* — with HOME ending the alarm outright,
and the tactile argument is real: both controls are unmistakable, blind-operable, and ending an alarm
should require the more deliberate reach. It is nevertheless a contextual override of the one rule
ADR 0026 § 2 makes absolute, so it stays a **hypothesis**. It must be tested against a child at
night, a half-asleep adult, an older person, a blind user and someone with limited motor control,
with particular attention to accidentally ending an alarm instead of snoozing it. No long press or
double press may be used to separate them.

**C2 — A running timer cannot be cancelled without the display.** Cancelling means finding the timer
and selecting it, which needs a visible surface. No control cancels a timer blind. This is a real
gap in the blind-operation principle for a future capability. It is **not** a reason to add a
control; it is a reason to design the timer's surface so that HOME plus one SELECT press reaches the
cancel action, and to verify that in real use.

**C3 — PREVIOUS / NEXT change visible content in `AMBIENT`.** A Group B event altering what is on the
panel sits close to the rule that transport never touches display state. It is permitted, because
`AMBIENT` is already lit and explicitly authorised and the display *state* does not change. The hard
boundary stands: they must never wake from `OFF`.

**C4 — Radio favourites have no domain model.** PREVIOUS / NEXT stepping through favourites presumes
a favourites concept that does not exist. Recorded as direction; it needs the collection/favourite
decision before implementation. ADR 0009 currently defines radio transport as ignored, and that
remains in force until then.

**C5 — Controlled shutdown has no control.** ADR 0026 § 8 deliberately removes an everyday power
button from the primary surface, which leaves shutdown without any physical path. Rear or underside
control, local administration only, or both, is an open decision — and neither this document nor
current code implements any of them.

**C6 — Proximity illumination during Night.** "Everything dark at night" and "controls fade up when
a hand approaches at night" cannot both be unconditional. Resolved in ADR 0026 § 9 by naming the
policy: `off` is the only implemented value and the default, so today's absolute-dark guarantee and
`DISPLAY_STATE_MACHINE.md` invariant 8 are preserved exactly. A deliberate human choice of
`on_approach` would amend that invariant when the hardware and the policy exist — not before.

**C7 — A message must not become a notification.** Situation 25 is the standard failure mode of this
class of feature. Personal messages appear as content and never acquire a badge, counter or
attention state. *Decided 2026-08-19 by ADR 0027 § 9:* arrival is one very restrained
`NOTIFICATION` sound plus a brief calm visual in the normal state, and **completely silent at
night** — no sound, no display wake, no illumination, no automatic playback. New does not mean
urgent. The conflict is resolved; the row stays here because the failure mode it names is permanent.

## 10. What only real hardware and real use can decide

- Whether HOME actually removes the need for a BACK control once browsing is deeper than one level.
- Whether focus wrapping reads as helpful or confusing, particularly to a three-year-old.
- Whether SELECT and VOLUME are reliably distinguished by hand in the dark with the chosen caps.
- Whether HOME's position and shape are found blind, and are not pressed by accident.
- Whether C1's snooze/end split survives half-asleep and non-visual use.
- Whether `on_approach` illumination is helpful or startling at night, and its false-positive rate
  when someone merely walks past or turns over in bed.
- Whether the minimum useful illumination level is still below the "disturbing in a fully dark
  bedroom" threshold.

These belong to `docs/hardware/RH1_VALIDATION_CHECKLIST.md` and are recorded in
`docs/product/USE_OBSERVATIONS.md` when measured.
