# Device UI principles

**Status:** Product/UX contract
**Date:** 2026-08-17

## Goal

AQENO should feel as immediate and self-explanatory as a good dedicated music device: few concepts,
clear hierarchy, direct feedback and no visible technical complexity. Classic iPod products are a
reference for that interaction quality, not a visual design to copy.

> AQENO is not a computer a child can operate. It is a device a child should not need to learn first.

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
5. **Physical first.** Volume, play/pause and physical-media launch use the physical controls where
   available. Touch complements those paths; it does not duplicate every one of them.
6. **Display is not a tablet.** Available area need not be filled. Whitespace, artwork, a title,
   optional chapter/track and restrained progress may be the complete playback surface. The display
   may then become quiet or turn off.
7. **Progressive disclosure.** An action appears only when the current context needs it. Technical
   availability alone does not earn permanent screen space.
8. **Reduction is product quality.** If two of ten possible functions matter now, show those two.
9. **Immediate, understandable feedback.** Touch and physical intentions visibly or audibly confirm
   recognition and outcome when policy permits. Feedback uses user meaning — starting, paused,
   volume changed, object not recognised — never backend terminology.
10. **Calm failures.** Technical detail belongs in local logs and adult diagnosis. Failure feedback
    obeys `FAILURE_STATES.md`: it never wakes a dark display, and Night policy may intentionally make
    it silent.
11. **No unavailable or commercial surfaces.** Product Principle P15 applies without exception on
    the box. An unavailable capability has no control, lock, badge, preview or upgrade prompt.

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

If an element can be removed without reducing usability, remove it by default.
