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
   the physical controls where available, and since ADR 0024 so does navigation: focus movement and
   selection have their own physical vocabulary. No function and no path to a function may require
   touching the panel. Touch complements those paths; it does not duplicate every one of them and it
   is never the only way in.
6. **Encoder-first information architecture.** Design for a rotating, pressing control first and let
   touch ride along — never the reverse. Every state answers four questions without instruction:
   where am I, what is selected, what will rotation do, what will a press do. Focus must be
   unmistakable from normal viewing distance, and never carried by colour alone.
7. **Display is not a tablet.** Available area need not be filled. Whitespace, artwork, a title,
   optional chapter/track and restrained progress may be the complete playback surface. The display
   may then become quiet or turn off.
8. **Progressive disclosure.** An action appears only when the current context needs it. Technical
   availability alone does not earn permanent screen space.
9. **Reduction is product quality.** If two of ten possible functions matter now, show those two.
10. **Immediate, understandable feedback.** Touch and physical intentions visibly or audibly confirm
   recognition and outcome when policy permits. Feedback uses user meaning — starting, paused,
   volume changed, object not recognised — never backend terminology.
11. **Calm failures.** Technical detail belongs in local logs and adult diagnosis. Failure feedback
    obeys `FAILURE_STATES.md`: it never wakes a dark display, and Night policy may intentionally make
    it silent.
12. **No unavailable or commercial surfaces.** Product Principle P15 applies without exception on
    the box. An unavailable capability has no control, lock, badge, preview or upgrade prompt.

## Accessible by default

Appliance simplicity is not confined to Kids UI. Large physical controls and touch targets, little
required text, clear hierarchy, audio feedback and shallow navigation benefit many people. Core
actions must not rely exclusively on fine motor control, dragging, swiping, double taps, long
presses, hidden gestures or fast reactions. This constrains ADR 0024's open back-navigation
question: if long press on NAV becomes Back, a second path back that needs no timing must exist, or
the rule does not survive this paragraph. That is a testing question, not a preference.

This does not claim compliance with every accessibility need. It means concrete needs should improve
the shared interaction language rather than automatically creating a labelled “senior”, “disabled”
or other parallel UI. Routine playback must remain possible without a smartphone, account, keyboard
or voice assistant.

## Kids Early

The preferred mental model is: present the physical object, AQENO plays. Core listening must not
require menu navigation. Each additional choice must justify the cognitive load it adds for a child
who cannot be expected to read.

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
