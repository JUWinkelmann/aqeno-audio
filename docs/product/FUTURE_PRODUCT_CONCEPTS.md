# Future Product Concepts

**Status:** Unscheduled product backlog — not Vertical Slice scope

**Date:** 2026-08-17

This catalogue preserves plausible product directions without making them requirements, milestones
or architecture work. Nothing here authorises implementation, a dependency, an interface or generic
infrastructure. YAGNI remains binding.

> AQENO may become internally capable without becoming complicated for a child.

AQENO remains a calm, physical and intuitive family audio device. The display supplies context,
emotion and immediate feedback, then recedes. It is not an invitation to build a tablet, game
platform or engagement surface.

## Classification

`Natural Extension` means existing AQENO concepts cover much of the product shape. `Product
Expansion` adds a materially new mode or responsibility. `Service Candidate` means remote
infrastructure could provide substantial value, not that cloud use is required or approved.

| Concept | Classification | Existing foundation |
|---|---|---|
| F1 Family Audio Messages | Natural Extension; Service Candidate for remote delivery | personal recordings, Actions, contextual display |
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
| F12 Profiles / Multiple Children | Product Expansion | Profile-scoped policy and resume |
| F13 Token to Action | Natural Extension | Action/Scene and Trigger are documented domain concepts |
| F14 Physical Interaction as UI | Natural Extension | physical-first UX and ADR 0013 |
| F15 Contextual Display | Natural Extension | display state machine and presentation boundary |
| F16 Quiet Display / Attention Policy | Natural Extension | existing DisplayPolicy and dark-room invariants |
| F17 Games/tablet/platform direction | Explicit Non-Goal | audio-first product principles |

Classification is not implementation order. A concept may move category when a concrete product
journey reveals different infrastructure or risk.

## F1 — Family Audio Messages

**High future product interest.** An authorised family member leaves a short audio message. The
Kids UI communicates only the emotional meaning — for example one heart — and tapping it plays the
message. The interaction is messaging without messaging UI: no inbox, chat list, unread counter,
text conversation or social-media metaphor.

Later journeys may consider replay, multiple messages or senders, a physical message token and
delivery within the home. Remote delivery is a separate optional service candidate. Before that,
AQENO needs an explicit privacy, authorisation, retention and deletion design; child-related audio
must not be collected merely because delivery makes it possible.

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

## F12 — Profiles / Multiple Children

Multiple people may eventually have distinct progress, favourites, allowed content, volume limits
and routines. Existing Profile-scoped rules keep this possible. The product journey must avoid
routine login and profile-selection screens; physical or contextual selection is preferable when it
is reliable and understandable. No identity mechanism is chosen here.

## F13/F14 — Token Actions and physical interaction

Physical tokens may eventually represent comprehensible Actions rather than only media: Dragon to
story, Moon to Good Night, Sun to Morning, Radio to station, Heart to message, Music Note to
playlist, Frame to Frame mode. This extends the existing Trigger/Action/Scene language and ADR 0013.

No generic Action engine is justified today. Generalisation is reconsidered only after several real
use cases need shared semantics; until then explicit assignments are preferable. Physical objects
are part of the UI because they can hide internal complexity behind an action a child understands.

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

## Feature review gate

Before any Device feature enters the roadmap, answer:

1. Does it support audio, family connection or a useful everyday function?
2. Can a child understand the interaction without explanation?
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

Passing this review permits roadmap consideration, not implementation. A roadmap milestone still
requires an explicit product decision.
