# Device UI principles

**Status:** Product/UX contract
**Date:** 2026-08-17

## Goal

AQENO should feel as immediate and self-explanatory as a good dedicated music device: few concepts,
clear hierarchy, direct feedback and no visible technical complexity. Classic iPod products are a
reference for that interaction quality, not a visual design to copy.

> AQENO is not a computer made easier for a target group. It is a dedicated device whose ordinary
> use should not need to be learned first.

The concrete navigation, RH1 layout and presentation direction are specified in
`DEVICE_UI_BLUEPRINT.md`. Its shorthand is: content first; controls second; technology invisible.
Artwork is navigation rather than decoration, and motion explains change rather than demanding
attention.

`TARGET_GROUP_UX_CONCEPTS.md` separately explores substantially different interaction models. AQENO
does not reduce adaptive interaction to larger type or fewer copies of the same layout, and it does
not infer an interaction model from a person's age.

The quality question is not whether a surface looks modern. It is whether a person understands
within seconds what they can do, and whether another element can be removed without making that
harder.

## Interaction rules

1. **Self-explanatory before feature-rich.** Do not compensate for a difficult interaction with a
   manual, tutorial, onboarding carousel, tooltip or explanatory copy. First simplify the action.
2. **Few mental models.** Normal Device UI uses product language, never implementation terms such as
   NFC, mount, sync state, media source, connectivity, storage, provider, service, adapter or cache.
3. **Shallow navigation.** Avoid nested settings and deep menus. Configuration belongs in the
   Management UI unless it is necessary for immediate use, pairing or recovery at the box.
4. **One clear primary action.** A state should present the action relevant to its context rather
   than a matrix of equally weighted controls.
5. **Physical first, touch optional.** Volume, play/pause, transport and physical-media launch use
   the physical controls where available, and since ADR 0024 so does navigation: focus movement,
   selection and the return to Home have their own physical vocabulary. No function and no path to a
   function may require touching the panel. Touch complements those paths; it does not duplicate
   every one of them and it is never the only way in. Every essential everyday action must also be
   performable **without looking** (ADR 0026 § 1).
6. **Encoder-first information architecture.** Design for a rotating, pressing control first and let
   touch ride along — never the reverse. Every state answers four questions without instruction:
   where am I, what is selected, what will rotation do, what will a press do. Focus must be
   unmistakable from normal viewing distance, and never carried by colour alone. What each control
   does in each state is normative in `docs/implementation/INTERACTION_MATRIX.md`; a surface that
   needs a control to mean something new is a design conflict to report, not to implement.
7. **Display is not a tablet.** Available area need not be filled. Whitespace, artwork, a title,
   optional chapter/track and restrained progress may be the complete playback surface. The display
   may then become quiet or turn off.
8. **Progressive disclosure.** An action appears only when the current context needs it. Technical
   availability alone does not earn permanent screen space.
9. **Reduction is product quality.** If two of ten possible functions matter now, show those two.
10. **Immediate, understandable feedback, physical first.** Touch and physical intentions visibly or
   audibly confirm recognition and outcome when policy permits. Feedback uses user meaning —
   starting, paused, volume changed, object not recognised — never backend terminology. Prefer the
   inherent feedback of the control and the result of the action itself (`PRODUCT_FOUNDATION.md`
   P20): a felt detent, a defined actuation point, audio that starts. Add an invented cue only where
   the outcome would otherwise be ambiguous, and never a sound per physical action by default.
11. **Calm failures.** Technical detail belongs in local logs and adult diagnosis. Failure feedback
    obeys `FAILURE_STATES.md`: it never wakes a dark display, and Night policy may intentionally make
    it silent.
12. **No unavailable or commercial surfaces.** Product Principle P15 applies without exception on
    the box. An unavailable capability has no control, lock, badge, preview or upgrade prompt.

## Accessible by default

Appliance simplicity is not confined to Kids UI. Large physical controls and touch targets, little
required text, clear hierarchy, audio feedback and shallow navigation benefit many people. Core
actions must not rely exclusively on fine motor control, dragging, swiping, double taps, long
presses, hidden gestures or fast reactions. ADR 0024 § A2 turns that into a flat product rule:
**normal everyday operation must not require long-press or double-press gestures.** The way out is
the HOME control, not a timed gesture (ADR 0026 § 4). Long press survives only for setup, service
and hardware cases.

Accessibility here is not a variant. AQENO must be usable by children, adults, older people and
people with motor or visual limitations **without looking like an assistive device** — one
interaction model, no separate Kids, Senior or Accessible operating logic, and mechanical adaptation
(larger, grippier caps) that changes ergonomics without changing electronics or logic
(ADR 0026 § 1). Optional spoken UI feedback is a recorded accessibility direction, not an
implemented capability, and needs no microphone.

This does not claim compliance with every accessibility need. It means concrete needs should improve
the shared interaction language rather than automatically creating a labelled “senior”, “disabled”
or other parallel UI. Routine playback must remain possible without a smartphone, account, keyboard
or voice assistant.

## Kids Early

The preferred mental model is: present the physical object, AQENO plays. Core listening must not
require menu navigation. Each additional choice must justify the cognitive load it adds for a child
who cannot be expected to read.

## Presentation levels

**A presentation level is not an age classification.** There is no child mode, senior mode or
disabled mode; a small child, an older person and an adult who simply prefers calm may all choose
the same level, and the interaction is identical for all of them.

| Level | What it shows |
|---|---|
| `VISUAL` | meaning carried by image, form and position; text is not required |
| `VISUAL_LABEL` | the same structure, with a short label confirming the visual meaning |
| `INFORMATIVE` | the same structure, plus counts, context, time and status |

A level changes **information density only**. It must never change navigation, available functions,
SELECT or PREVIOUS/NEXT semantics, HOME, touch capability or domain behaviour — that would be a
second interaction architecture, which AQENO does not have. The experience configurations of
`PRODUCT_FOUNDATION.md` § 4 map onto this one axis rather than adding another; no profile defaults
to `VISUAL`, which stays a deliberate preference rather than an inference about anyone.

> **Text confirms meaning. Text does not create core meaning.**

Text remains valuable for precision, titles, sender names, context, learning support and adults.
The rule is about where meaning *originates*. Where information is unavoidably textual, say so
honestly rather than claiming accessibility that is not there.

## Context actions

Secondary actions are a **visual action carousel**, not a text menu: one dominant action object,
neighbours hinted, SELECT rotating between them and its press executing the focused one. HOME still
rescues, and a visible action may also be tapped — the same action, never a touch-only path.

Deliberately small: two to four frequent actions. A surface that appears to need more has an
information-architecture problem, and a "More…" bin is semantically weak for anyone who cannot read
it. Before an action earns a place, work through: can a strong visual object carry it; is the
silhouette distinguishable at distance; is the metaphor plausible for a pre-reader; is text only
confirmation; if text is required to understand it, does it belong on the device at all, or in the
administration client?

**An unknown symbol is only an unknown symbol.** Icon libraries may serve as development reference
and never as AQENO's language.

Now Playing does not gain permanent secondary controls: context actions appear only after a
deliberate SELECT interaction and disappear again.

## What stays outside

Wi-Fi configuration, library management, NFC assignment, accounts, backup, integrations,
diagnostics, advanced audio settings and optional services are presumed to belong in the separate
Management UI. An on-device exception requires a concrete immediate-use, pairing or recovery need;
the existence of a setting is not sufficient.

## Review before adding a Device UI element

1. Must this function be available on the box?
2. Must it remain visible in this state?
3. Does a physical control solve it better?
4. Is the action understandable without explanation?
5. Can one navigation step be removed?
6. Can AQENO make the correct decision from context?
7. Is this actually administration for the Management UI?
8. Does this increase a child's cognitive load?
9. Does this make digital audio simpler, or merely make AQENO more feature-rich?
10. Does a core path require precision, timing, reading or an external personal device that the
    user may not have?
11. Is every part of this reachable and operable with no touch at all (ADR 0024)?

If an element can be removed without reducing usability, remove it by default.
