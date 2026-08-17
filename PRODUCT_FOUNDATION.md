# AQENO Player — Product Foundation

**Status:** v0.2  
**Date:** 2026-08-17  
**Purpose:** Product foundation and decision frame for discovery and implementation.

## 1. Purpose

AQENO is not a cheaper Toniebox clone and not a tablet with a child-friendly skin. It is an **open, adaptive, audio-first player platform** that makes audio exceptionally simple while preserving freedom of hardware, content and interaction.

> **AQENO adapts to people — people should not have to adapt to the player.**

The first product focus is **AQENO Kids**. The same core should support **AQENO Easy**, a non-stigmatising simplified experience suitable for older users and anyone who benefits from reduced complexity.

## 2. Product position

> **The independence of a Toniebox with the freedom of a tablet — without turning an audio player into a tablet.**

AQENO sits between intuitive but closed audio systems and flexible but distracting general-purpose devices.

- Audio-first, not screen-first.
- Open content, not proprietary media objects.
- Adaptive interaction, not a fixed age-specific UI.
- Physical controls for frequent actions; touch for context and selection.
- Local-first operation; connected services are optional enhancements.
- No product mechanics designed to maximise listening time.

## 3. Product principles

### P01 — AQENO adapts to people
Interface complexity, text density and navigation evolve with the user's capabilities and preferences.

### P02 — Content, not apps
Users choose a story, station, podcast or album — not a provider, protocol or file type.

### P03 — Local first
Core playback and already available content remain usable without cloud connectivity.

### P04 — Open content
AQENO does not own or lock in the user's media. Standard formats, feeds and streams remain usable outside AQENO.

### P05 — Bring your own hardware
Where practical, AQENO uses open standards and replaceable commodity components: USB-C power, external power banks, supported SBCs, standard audio interfaces and printable enclosures.

### P06 — Frequent actions are physical
High-frequency actions should work through touch and muscle memory without screen navigation.

### P07 — Screen when useful, screenless when possible
The display adds context, discovery and configuration, but is not required for fundamental playback actions.

### P08 — Care, not surveillance
Guardian/manager functionality supports boundaries and assistance without unnecessary behavioural tracking.

### P09 — Simple by default, powerful by choice
Capabilities appear when useful. Complexity is not exposed merely because AQENO supports it.

### P10 — No lock-in
Avoid proprietary batteries, chargers, media objects and unnecessary cloud dependencies.

### P11 — Audio does not imply visual activity
Playback and visual activity are independent. Audio may continue with every display and light completely off.

### P12 — AQENO does not optimise for engagement
No infinite feeds, streaks, attention notifications, paid child-facing placements or mechanics intended to maximise usage time.

### P13 — Fast to audio, fast to invisible
AQENO should become usable quickly after power-on or wake, and should be able to become visually quiet just as quickly. Boot, wake and display behaviour are product experience, not implementation details.

### P14 — Ambient display is explicit, not default
The display may support useful ambient experiences such as a digital photo frame, clock or artwork, but these modes must never emerge merely because the device is idle. They are explicitly enabled by the person authorised for the active experience profile.

## 4. Adaptive experience

AQENO should use a shared capability model rather than separate rigid products for each age.

| Stage / mode | Primary UI | Typical navigation | Screen role |
|---|---|---|---|
| Kids Early | Images, minimal/no text | NFC + physical controls | Optional/discovery |
| Kids Reader | Images + labels | NFC + touch | Selection and learning |
| Kids Explorer | Library, categories, search | Touch + NFC | Primary discovery surface |
| Easy | Large tiles + large text | Touch + physical controls | Simple contextual surface |
| Standard | Full library UI | Touch + controls | Full interface |

Transitions remain manually controllable. AQENO may suggest a different complexity level but must not silently decide that a child or other user is ready for it.

## 5. Physical interaction

> **Frequent actions are physical. Contextual actions are visual.**

Reference control set:

| Control | Primary action | Reason |
|---|---|---|
| Rotary encoder | Volume | Fast, eyes-free, continuous |
| Encoder press | Play / pause | Central and usable in darkness |
| Previous button | Previous / contextual rewind | Frequent playback action |
| Next button | Next / contextual skip | Frequent playback action |
| Touchscreen | Library, selection, search, settings | Context-dependent interaction |
| NFC | Content/action shortcut | Physical, intuitive, optional |

Do not add dedicated Home, Back, Favourite or Menu buttons unless user testing proves them necessary.

## 6. Dark-room requirement

> **AQENO must be usable in a completely dark bedroom without requiring the display or any light to turn on.**

This is a core product requirement, not an energy-saving feature.

During bedtime playback AQENO must be able to:

- turn the display fully off while audio continues;
- turn off decorative and status LEDs;
- suppress system sounds and visual flashes;
- keep volume and play/pause physically operable;
- apply a configurable night-time volume ceiling;
- optionally apply a sleep timer or bedtime scene;
- remain dark when a physical playback control is used.

Playback state and visual state are separate architectural concepts.

### Display-state model

AQENO treats the display as an explicit state machine rather than a generic always-on UI surface:

- **OFF** — panel dark; no visual activity;
- **DIM** — minimal low-luminance information where explicitly useful;
- **INTERACTIVE** — active touch/navigation interface;
- **AMBIENT** — deliberately enabled passive visual mode such as selected photos or artwork;
- **SETUP** — installation, onboarding or administrative configuration.

For **Kids Early**, the default during audio playback is `OFF` after a short configurable interaction timeout. Playback changes, buffering and chapter transitions must not wake the display unless the user explicitly requests visual interaction.

`AMBIENT` is not a fallback for inactivity. It is a scene/capability that must be intentionally enabled.

## 7. Open physical media and NFC

AQENO preserves the haptic strength of figure-based systems without requiring proprietary figures. NFC is an open shortcut layer, not the content store.

- A tag may identify an item, collection, profile, scene or action.
- Tags may live in 3D-printed figures, cards, wooden tokens, stickers, key rings or existing toys.
- AQENO can publish reference dimensions and printable holders for commodity NFC tags.
- The same object may evolve with the user: one story at age three, a collection/category later.
- NFC remains optional; the library never depends on owning physical tokens.

## 8. Content model

AQENO presents one content library regardless of technical source. Initial types:

- local audio files/folders;
- audiobooks and long-form audio with reliable resume;
- podcasts/RSS;
- internet radio and compatible HTTP streams;
- playlists/collections;
- personal recordings/messages.

Content identity is independent from launch method. NFC, touchscreen and remote launch use the same metadata, progress and availability state.

## 9. AQENO Actions, Scenes and Context

NFC and touch can trigger more than media. **Actions** are reusable commands; **Scenes** combine settings into meaningful contexts.

### Example: Sleep scene

- start an approved bedtime playlist;
- set/cap volume;
- switch display and LEDs off;
- suppress unnecessary system sounds;
- apply a sleep timer;
- optionally restrict autoplay/available content.

Other candidates: **Travel**, **Morning**, **Quiet time**.

Scenes are transparent and user/Guardian-defined, not driven by opaque recommendation algorithms.

## 10. Guardian / manager model

Use roles rather than hard-coded parent/child relationships:

- **User** — consumes and controls permitted content.
- **Manager** — curates content and experience boundaries.
- **Owner** — controls device/account ownership and management rights.

This supports both parent → child and family member → AQENO Easy user.

Possible management capabilities include content curation, UI complexity, volume limits, usage windows, sleep behaviour, NFC assignment, offline preparation and optional remote content delivery.

> **AQENO enables care, not surveillance.**

Detailed behavioural histories should not be a default feature.

## 12. Startup, wake and perceived readiness

Fast startup is a first-class product requirement. AQENO should feel like an appliance, not a general-purpose computer.

Initial validation targets for Reference hardware:

- **physical input response after wake:** perceptibly immediate; target < 500 ms;
- **display wake to interactive UI:** target <= 1 s;
- **warm application resume:** target <= 2 s;
- **cold power-on to basic physical control readiness:** target <= 8 s;
- **cold power-on to interactive home UI:** target <= 10 s.

These are product targets to validate during feasibility work, not promises for every Community hardware configuration.

The architecture should favour staged readiness: physical controls, cached state and resumable local audio may become available before every optional service or remote integration has initialised.

## 12. Hardware philosophy

AQENO software runs on a **defined range of hardware**, not one inseparable board. Freedom is bounded by supportability.

### Compatibility levels

- **Reference** — tested and documented by AQENO.
- **Compatible** — satisfies published AQENO interfaces/requirements.
- **Community** — may work, without official guarantees.

### Reference hardware principles

- slim core player;
- USB-C power;
- ordinary external power bank is a valid mobile-power option;
- no proprietary battery requirement;
- initial reference display: approximately 5–7 inch touch;
- rotary encoder + minimal playback buttons;
- optional NFC;
- standard/replaceable audio components where practical;
- simple printable enclosure designs.

A future commercial device may integrate components for manufacturing efficiency while preserving openness wherever reasonable.

## 13. Capabilities beyond a Toniebox

AQENO differentiates through architecture, not feature accumulation.

| Capability | AQENO opportunity |
|---|---|
| Adaptive UX | Image-only interaction can grow into a full audio library. |
| Open NFC | Any suitable object can become a content/action token. |
| Unified content | Files, podcasts, streams and personal audio appear in one library. |
| Dynamic physical objects | One token can represent increasing depth as the user grows. |
| Reliable resume | Progress follows content across NFC, touch and remote launch. |
| Personal audio | Family can provide stories or voice messages. |
| Multi-user | Profiles can change through touch or physical identity tokens. |
| Offline preparation | A travel mode can prepare approved content before leaving home. |
| Scenes | Bedtime, travel and other contexts alter behaviour coherently. |
| Remote curation | Managers can add/organise content without touching the device. |
| Follow-me potential | Future players may continue playback across rooms/devices. |
| Standard connectivity | Headphones/speakers and other standard audio paths fit the same content model. |
| Deliberate ambient mode | Selected photos, artwork or simple information can use the display when explicitly enabled without turning AQENO into a distraction-first device. |

## 14. Product family

### AQENO Kids
Autonomous, safe and increasingly capable audio use from early childhood onward.

### AQENO Easy
A simplified, non-stigmatising audio experience for users who prefer or benefit from reduced complexity. It is not defined solely as a senior product.

### Shared core
Both share the player engine, content model, role model, hardware abstraction and adaptive UI primitives. Differences should primarily be configuration and experience, not separate codebases.

## 15. Business and trust boundaries

- Core local playback must not require a subscription.
- No advertising or paid placement in the child-facing interface.
- Optional cloud services may later finance remote sync, backups or family management.
- If AQENO cloud services disappear, local content and core playback continue working.
- Commercial streaming integrations are added only where licensing and technical terms permit them.
- Final open-source/commercial licensing remains an explicit future decision; architecture must not accidentally foreclose either path.
- Kids ambient display modes must be opt-in and Manager/Owner controlled by default; arbitrary remote image feeds must never appear without explicit authorisation.

## 16. Initial hypotheses to test

These are hypotheses, not facts:

1. A young child can operate AQENO independently without reading.
2. A display can increase capability without increasing screen dependence.
3. Three primary physical controls plus NFC are sufficient for routine playback.
4. AQENO can offer an optional ambient/photo-frame mode without increasing distraction when activation, timing and content authority are explicit.
5. A staged boot path can make AQENO feel appliance-like even on commodity SBC hardware.
4. Adaptive complexity creates meaningful longevity beyond the typical early-childhood audio-box period.
5. Open physical media retains the haptic benefit of figures without proprietary content lock-in.
6. One platform can serve Kids and Easy without compromising either experience.
7. Managers value remote curation more than detailed monitoring.
8. A slim USB-C player with optional commodity power bank is preferable to a permanently integrated battery for the reference DIY platform.

## 17. Next discovery work

### Journey 01 — three-year-old child

Map the complete experience from unboxing through Guardian setup, first content, independent playback, NFC use, physical controls, discovery, bedtime listening and falling asleep in a completely dark room.

Every interaction is classified as **PHYSICAL**, **TOUCH**, **NFC**, **REMOTE** or **AUTOMATIC**. Anything that does not make Kids Early simpler remains outside that interface.

Subsequent journeys:

1. six-year-old beginning to read;
2. ten-year-old independent explorer;
3. parent/Guardian managing content and boundaries;
4. independent AQENO Easy user;
5. AQENO Easy user assisted remotely by family.

## 18. Working definition

> **AQENO is an open, adaptive, audio-first player platform that gives users the simplicity they need without taking away the freedom they may want later.**

This foundation intentionally does **not** commit to a specific SBC, UI framework, audio engine or commercial model before user journeys and feasibility work provide sufficient evidence.
