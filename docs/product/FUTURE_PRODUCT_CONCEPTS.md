# Future Product Concepts

**Status:** Unscheduled product backlog — not Vertical Slice scope

**Date:** 2026-08-17

This catalogue preserves plausible product directions without making them requirements, milestones
or architecture work. Nothing here authorises implementation, a dependency, an interface or generic
infrastructure. YAGNI remains binding.

**Nothing is removed from this catalogue for lacking market differentiation** (ADR 0015 § 2). A
concept earns implementation by making AQENO better for the person using it, not by being unique. In
particular, `F1 Send to AQENO` is no longer defined by whether a paid service follows: a parent
sending a child a personal message from a trip, a heart appearing, a tap, a familiar voice, is
sufficient value on its own (ADR 0015 § 6). Whether AQENO Connect ever exists is a separate, later
decision.

> AQENO may become internally capable without becoming complicated for the person using it.

AQENO remains a calm, physical and intuitive audio device for individuals and families. The display
supplies context, emotion and immediate feedback, then recedes. It is not an invitation to build a
tablet, game platform or engagement surface.

## Classification

`Natural Extension` means existing AQENO concepts cover much of the product shape. `Product
Expansion` adds a materially new mode or responsibility. `Service Candidate` means remote
infrastructure could provide substantial value, not that cloud use is required or approved.

| Concept | Classification | Existing foundation |
|---|---|---|
| F1 Send to AQENO / personal audio messages | Natural Extension; Service Candidate for remote delivery | personal recordings, Actions, contextual display |
| F2 Digital Family Frame | Product Expansion | explicit Ambient state and visual-source authority |
| F3 Sleep / Good Night | Natural Extension | Scene, Night policy, sleep timer, physical Actions |
| F4 Sleep Timer | Natural Extension | configuration contract already defines timer and fade |
| F5 Wake-up / Morning | Product Expansion | Scene and scheduled/contextual display concepts |
| F6 Playback Continuity | Natural Extension | resume is already `(ContentItem, Profile)` |
| F7 Internet Radio | Natural Extension | `RADIO_STREAM` and HTTP Source already exist |
| F8 Podcasts | Natural Extension | podcast episode kind and MVP theme already exist |
| F9 Bluetooth Speaker | Product Expansion | audio/hardware adapter boundary |
| F10 External Audio Services | Service Candidate | optional service adapters and Source separation |
| F11 Ambient Audio | Natural Extension | ordinary local content plus physical assignment |
| F12 Multiple users and contexts | Product Expansion | Profile-scoped policy and resume |
| F13 Token to Action | Natural Extension | Action/Scene and Trigger are documented domain concepts |
| F14 Physical Interaction as UI | Natural Extension | physical-first UX and ADR 0013 |
| F15 Contextual Display | Natural Extension | display state machine and presentation boundary |
| F16 Quiet Display / Attention Policy | Natural Extension | existing DisplayPolicy and dark-room invariants |
| F17 Games/tablet/platform direction | Explicit Non-Goal | product identity, ADR 0023 § 3 |
| F18 Visual timer and timer presets | Natural Extension; **first time capability** | time pillar, ADR 0025 § 3 |
| F19 Clock, alarms and radio-alarm behaviour | Product Expansion; waits for F18 | time pillar, ADR 0025 § 3 |

Classification is not implementation order. A concept may move category when a concrete product
journey reveals different infrastructure or risk.

## F1 — Send to AQENO

**High future product interest and likely Service Candidate.** An authorised contact records a
short audio message for an AQENO device. The recipient sees only the human meaning—for example one
heart—and tapping it plays the familiar voice. This may connect parent and child, grandchildren and
grandparents, family and an independently listening or assisted person. It is not a medical,
emergency, medication or care-monitoring service.

The interaction is messaging without a messenger: no inbox, chat threads, unread counter, text,
keyboard, read receipt, contact management or social-media metaphor on the recipient Device UI. A
sender may use a more capable Web or smartphone flow—choose an authorised AQENO, record, send—while
the recipient only needs to understand: there is a heart, tap it, hear someone they know. This
asymmetry is intentional.

Remote delivery could justify a paid optional service because authentication, authorised senders,
storage, encryption, delivery, abuse prevention, privacy and deletion are real operated work. It
does not justify a local paywall: without the capability, no heart, disabled control, tier badge or
upgrade surface exists on the device. Sender-side accounts must never become a prerequisite for
ordinary local Core playback.

Later journeys may consider replay, multiple messages or senders, a physical message token and
delivery within the home. Before any remote implementation, AQENO needs explicit privacy,
authorisation, retention, deletion and vulnerable-user safeguards. Personal audio must not be
collected merely because delivery makes it possible.

## F2 — Digital Family Frame

Selected local family photos or albums, optionally with a quiet clock, may use the existing
`AMBIENT` state. This is an explicitly activated Frame mode, not an automatic idle fallback and not
continuous accompaniment to play or listening. `DISPLAY_BEHAVIOR.md` remains the authoritative
contract for attention, schedules, source approval and Night override.

## F3/F4 — Good Night and Sleep Timer

A Moon token or adult configuration may activate a transparent Sleep Scene: reduce UI and volume,
start approved audio, run a timer, fade gently and turn the display off. The child's model may be
only “present moon, good night”; configuration belongs in the Management UI.

The Sleep Timer also remains independently useful. Possible end conditions include elapsed time,
chapter end, track end or current-work end. Exact semantics are decided only with the implementing
journey. Existing defaults for duration, fade and pause/stop do not implement the feature.

## F5 — Wake-up / Morning

A deliberately configured Morning Scene may start gentle audio at a defined volume and show a quiet
morning image or status. A Sun token may invoke it without exposing an alarm-clock application to a
child. Scheduling, reliability after power loss and guardian expectations require a separate product
and safety review before implementation.

## F6 — Playback Continuity

Core resume is not merely future work: `RESUME_BEHAVIOR.md` already defines progress per
`(ContentItem, Profile)` and the Vertical Slice implements it across touch and NFC launch. Future
work is the multi-person experience around that capability; it must not add login or profile-choice
friction to routine child use.

## F7/F8 — Curated radio and podcasts

Internet radio and podcasts are already MVP themes and domain content kinds, not new architectural
directions. The future product concepts are their child-appropriate curation surfaces: a Radio token
may launch an adult-configured station, and selected podcast shows may expose artwork, episode and
progress without an open search engine. Feed refresh, download and caching remain undecided until
implemented.

## F9 — Bluetooth Speaker

AQENO may accept external Bluetooth audio and react with a reduced contextual display. Pairing and
device management belong in an adult setup/management context. Bluetooth source routing, volume
authority, privacy and coexistence with AQENO playback require a measured hardware/product spike;
the current audio port is not extended in anticipation.

## F10 — External Audio Services

Legitimate provider integrations may become Source/service adapters when an official API, licence,
technical path and commercial terms all permit them. Provider names are not promises. AQENO does
not reverse engineer proprietary services, imitate credentials or bypass protection. Local Core
playback remains independent.

## F11 — Ambient Audio

White noise, rain, forest, sea and other calm sounds can be ordinary approved local content. A
cloud-shaped token launching rain is a physical assignment, not a reason for a new media subsystem.

## F12 — Multiple users and contexts

Multiple people may eventually have distinct progress, favourites, allowed content, volume limits
and routines. The same Core may support child, adult, independent and assisted contexts without
turning those labels into editions or domain roles. Existing Profile-scoped rules keep this
possible. The product journey must avoid routine login and profile-selection screens; physical or
contextual selection is preferable when it is reliable and understandable. No identity, persona or
theme mechanism is chosen here.

## F13/F14 — Token Actions and physical interaction

Physical tokens may eventually represent comprehensible Actions rather than only media: Dragon to
story, Moon to Good Night, Sun to Morning, Radio to station, Heart to message, Music Note to
playlist, Frame to Frame mode. This extends the existing Trigger/Action/Scene language and ADR 0013.

No generic Action engine is justified today. Generalisation is reconsidered only after several real
use cases need shared semantics; until then explicit assignments are preferable. Physical objects
are part of the UI because they can hide internal complexity behind an action a person understands.
A story figure, jazz card, news card or large distinctly shaped token differs in context, not in its
underlying Trigger/Action principle.

## F15/F16 — Contextual and quiet display

The display may take one relevant role at a time: restrained playback context, a family-message
heart, dark Good Night state, quiet Morning state, approved photos in Frame mode, or a dark/quiet
idle state. It is never a permanent dashboard.

This is mostly an evolution of existing `DisplayPolicy`, `DISPLAY_BEHAVIOR.md` and
`DEVICE_UI_PRINCIPLES.md`: brief feedback, then reduction, dimming or `OFF` according to context.
No gamification or animation may optimise screen time.

## F17 — Explicit non-goal: games and general computing

AQENO is not currently a game console, app platform, video portal, browser, YouTube device or
general child tablet. Raspberry Pi and touch capability do not create a product requirement. Any
future interactive exception requires its own review against the audio-first, attention and child
complexity principles; it does not establish a platform direction.

## F18 — Visual timer and timer presets

A timer is a natural AQENO time function and is configurable locally as well as through
administration. Local interaction may be as small as: choose timer, rotate SELECT to set the duration,
press SELECT to start (`INTERACTION_MATRIX.md` § 5). Remaining time is shown graphically — a total area or circle whose visible share
decreases — so a person who cannot read a numeric time still understands it. The general principle
is used; no protected product design is copied.

Presets are prepared in the web client — name, duration, optional artwork, optional completion
sound, optional profile assignment — and reuse the existing profile and content-assignment
mechanisms including bulk assignment. No new user or permission architecture.

A timer may run while audio plays. The UI must show that a timer is active without permanently
displacing Now Playing, and completion must resolve against audio deliberately rather than as a
second uncoordinated source. ADR 0025 § 3 holds the binding constraints.

## F19 — Clock, alarms and radio-alarm behaviour

**Sequenced behind F18** (ADR 0025 amendment): clock, alarm, radio-alarm behaviour and sunrise are
prioritised only after the visual timer is complete and validated in use. The vision below is
unchanged; only the order is.

AQENO may work as a modern radio alarm: clock, alarms, recurring alarms, audio as the alarm source,
configurable alarm volume with gradual increase, and a display wake-up visualisation — dark, slowly
rising brightness, visual sunrise, then audio. A small panel is not a room wake-up light and must
not be presented as one; real indirect lighting stays a possible optional hardware capability.

Two constraints are already binding (ADR 0025 § 3): a network-sourced alarm needs a local fallback,
and a scheduled alarm is a third path out of `OFF` that requires an explicit amendment to
`DISPLAY_STATE_MACHINE.md` invariant 4 before any scheduler exists. Where the configured mode
demands complete darkness, complete darkness wins.

## Feature review gate

Before any Device feature enters the roadmap, answer:

1. Does it support at least one pillar — audio, time or personal connection (ADR 0023)?
2. Can the intended user understand the interaction without explanation?
3. Can physical interaction make it simpler?
4. Must it be visible on the display at all?
5. Can complex configuration move to the Management UI?
6. Does it unnecessarily increase screen time?
7. Does it make AQENO more like a tablet?
8. Does the core idea work local-first?
9. Does it require an external service?
10. Is it Core, optional comfort or service functionality?
11. What new privacy or security obligations does it create?
12. Is the product and maintenance cost justified?
13. Does it make digital audio simpler, or merely make AQENO more feature-rich?

Passing this review permits roadmap consideration, not implementation. A roadmap milestone still
requires an explicit product decision.
