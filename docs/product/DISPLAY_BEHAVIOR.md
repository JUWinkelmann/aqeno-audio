# AQENO Display Behaviour

**Status:** Product/UX guardrail for discovery and implementation  
**Date:** 2026-08-17

## Purpose

AQENO has a display, but must not become a display-centric device. The screen provides context when useful and disappears when it would compete with listening, play, rest or social interaction.

> **The display is a capability, not the centre of the product.**

> **The AQENO display should recede, not simply turn off.**

## Core rules

1. **Audio playback never requires visual activity.**
2. **Playback events do not wake the display by default.**
3. **Kids modes default toward less visual stimulation, not more.**
4. **Ambient content is explicit and authorised, never an automatic idle fallback.**
5. **The person who may enable or configure ambient behaviour depends on the active ownership/experience model.**
6. **Dark-room operation always overrides decorative display behaviour.**
7. **A screen timeout must never pause or interrupt audio.**

## Display states

| State | Meaning | Touch | Typical use |
|---|---|---:|---|
| OFF | Panel fully dark | Wake gesture may be accepted | Listening, sleep, inactivity |
| DIM | Glanceable, deliberately reduced presentation | Wake only | Brief Now Playing context during playback |
| INTERACTIVE | Full active UI | Yes | Browse, choose, search, configure |
| AMBIENT | Passive approved visual content | Optional | Photo frame, artwork, simple information |
| SETUP | Bounded appliance setup | Yes | Pairing, recovery, simple choices |

Transitions are explicit application behaviour and must not be delegated blindly to desktop-environment defaults.

## Kids default

For `Kids Early`:

- during active playback, follow `INTERACTIVE → DIM → OFF` with conservative, configurable
  Reference-prototype timings;
- `DIM` is a presentation form, not an additional domain/display state: no visible touch controls,
  no navigation and no attention-seeking animation;
- when playback is idle, inactivity follows the existing path to `OFF` without entering `DIM`;
- physical volume, play/pause and next/previous remain functional while `OFF`;
- chapter changes, buffering, metadata updates and remote sync do not wake the display;
- touching the display may wake directly into the least distracting relevant view;
- bedtime/night scenes force `OFF`, skip glanceable `DIM` and prohibit `AMBIENT`.

### Glanceable Now Playing experiments

The Reference Hardware should test, without selecting a final variant yet:

1. small artwork plus title;
2. title plus chapter/episode;
3. title plus restrained progress;
4. title only.

`INTERACTIVE` remains the complete Now Playing UI with artwork, title, chapter/episode, progress and
available interaction. `DIM` is not that same screen with a lower brightness. The presentation layer
must deliberately remove controls and visual detail. In shorthand: `INTERACTIVE` means interact,
`DIM` means glance, and `OFF` means disappear.

## Ambient / digital photo frame

AQENO may support a digital photo-frame or artwork mode because the hardware already contains a useful display. This is **not** the default idle behaviour.

Glanceable `DIM` during playback is not Ambient. `AMBIENT` remains the explicitly enabled and
authorised photo-frame/artwork mode, and the invariant remains unchanged: **Ambient is never an
automatic fallback for inactivity.** AQENO shows no automatic idle clock or date.

### Recommended authority for child profiles

- disabled by default;
- enabled/configured by `Manager` or `Owner`;
- source collections are explicitly selected;
- optional schedules define when it may run;
- normally runs while AQENO is otherwise idle, not as visual accompaniment to an audio story;
- bedtime/night scenes override it;
- no arbitrary internet feed, recommendations or advertisements;
- a child may optionally choose among already approved ambient scenes if the Manager enables that capability.

### Easy / Standard

For an independent `Easy` or `Standard` user, the `Owner/User` may enable and configure ambient behaviour directly. A Manager may assist only where management rights were granted.

## Content authority

Ambient visuals have their own permission boundary. Permission to play audio does not automatically grant permission to display arbitrary images.

Potential sources, from safest to most open:

1. local approved album;
2. Manager-curated synced album;
3. personal artwork/covers already on the device;
4. approved remote family album;
5. third-party online sources — future, explicit opt-in only.

## Distraction tests

An ambient feature should be rejected or constrained if it:

- repeatedly attracts a child's attention away from play or listening;
- changes images too rapidly;
- uses animation for engagement rather than information;
- introduces notifications, badges or calls to action;
- wakes during bedtime;
- cannot be disabled cleanly by the responsible role.

## Startup and wake

The display experience must support appliance-like readiness.

Reference validation targets:

- physical input response after wake: < 500 ms target;
- display wake to interactive UI: <= 1 s;
- warm application resume: <= 2 s;
- cold boot to basic physical control readiness: <= 8 s;
- cold boot to interactive home UI: <= 10 s.

Prefer staged startup. AQENO should not block local playback or physical control while optional network/cloud integrations initialise.

## Open questions for user testing

- Should a touch wake reveal the currently playing cover or the home screen?
- Which of the four glanceable Now Playing variants is useful without drawing attention?
- Are the conservative Kids Early `DIM` timing and brightness comfortable in real use?
- Should Ambient stop immediately when audio starts, or may Managers choose otherwise?
- How long should interaction timeouts be for Kids Early, Reader, Easy and Standard?
- Which visual transitions feel calm rather than attention-seeking?
- Should a child be able to invoke an approved photo scene through an NFC Action?
