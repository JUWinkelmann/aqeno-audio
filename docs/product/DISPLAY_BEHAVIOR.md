# AQENO Display Behaviour

**Status:** Product/UX guardrail for discovery and implementation  
**Date:** 2026-08-17

## Purpose

AQENO has a display, but must not become a display-centric device. The screen provides context when useful and disappears when it would compete with listening, play, rest or social interaction.

> **The display is a capability, not the centre of the product.**

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
| DIM | Minimal, deliberately reduced output | Yes | Optional clock/progress where permitted |
| INTERACTIVE | Full active UI | Yes | Browse, choose, search, configure |
| AMBIENT | Passive approved visual content | Optional | Photo frame, artwork, simple information |
| SETUP | Onboarding/admin state | Yes | Pairing, network, maintenance |

Transitions are explicit application behaviour and must not be delegated blindly to desktop-environment defaults.

## Kids default

For `Kids Early` and similar profiles:

- after an interaction timeout during playback, transition to `OFF`;
- physical volume, play/pause and next/previous remain functional while `OFF`;
- chapter changes, buffering, metadata updates and remote sync do not wake the display;
- touching the display may wake directly into the least distracting relevant view;
- bedtime/night scenes force `OFF` and may prohibit `AMBIENT`.

## Ambient / digital photo frame

AQENO may support a digital photo-frame or artwork mode because the hardware already contains a useful display. This is **not** the default idle behaviour.

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
- Is a very low-brightness progress view useful, or is fully `OFF` preferable in Kids modes?
- Should Ambient stop immediately when audio starts, or may Managers choose otherwise?
- How long should interaction timeouts be for Kids Early, Reader, Easy and Standard?
- Which visual transitions feel calm rather than attention-seeking?
- Should a child be able to invoke an approved photo scene through an NFC Action?
