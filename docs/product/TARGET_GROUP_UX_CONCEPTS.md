# AQENO Interaction Model Concepts

**Status:** UX discovery; not an implementation contract
**Date:** 2026-08-18
**Applies to:** exploration of Kids Early, Kids Reading, Adult / Kitchen and Accessible interaction
models on Reference Hardware 1

## Purpose and boundaries

AQENO may support substantially different ways of finding and operating content while retaining one
product identity and one Core:

> **Same AQENO. Same visual language. Different interaction models.**

The concepts below are design hypotheses for different use situations. They do not assign an
interface by age, commit all four models to implementation, create product editions or authorise a
generic profile-rendering architecture. A person chooses an interaction model according to need and
preference; AQENO does not infer it from age.

Only existing capabilities may be treated as current: content items and chapters, artwork, content
kind, playback and resume per profile, semantic Previous / Play-Pause / Next / Volume, profiles,
roles and display policy. Collections exist in the documented domain model but are not implemented
in the current slice. Radio streams, podcasts and remote sources fit the source/content model, but
their discovery and ingestion experiences are not current Device UI capabilities. Favourites,
personal messages and remote Send to AQENO remain future concepts.

These concepts share:

- the AQENO visual language, typography, artwork treatment and motion rules;
- content-first presentation without app, provider, desktop or smartphone metaphors;
- the display states `INTERACTIVE`, `DIM`, `OFF`, `AMBIENT` and `SETUP`;
- `Previous`, encoder Volume / Play-Pause and `Next` hardware semantics;
- local-first operation, invisible technology and absence of locked or unavailable controls;
- a separate Management UI boundary; and
- true visual silence under `OFF` and Night policy.

The interaction model changes navigation structure, information hierarchy, choice architecture and
the division of work between touch and physical controls. It is not a theme or font-size preset.

## Concept A — Kids Early

### Mental model and hierarchy

**“I recognise what I want to hear.”** Familiar artwork or a physical token identifies a work.
Hierarchy is artwork first, current/selected state second and text only as non-essential support.
The child is never required to understand a library, category or source.

### Navigation, Home and content selection

- Home is the content selection surface: two or three large, spatially stable works at once.
- Three is the current vertical-slice maximum, not proof that every child should see three. A
  two-choice variant is a necessary comparison case.
- A single tap on artwork starts the work and opens Now Playing. No confirmation or detail screen.
- No hidden swipe, list, category label, back stack or carousel pagination is required.
- Previous and Next remain playback commands, not focus navigation, unless a later user test and
  semantic-input decision explicitly change that contract.
- NFC may bypass the screen entirely when available.

### Now Playing

- One very large artwork image dominates the frame.
- Playback state is conveyed with one simple symbol or restrained visual state; title and chapter
  may be absent when recognition remains unambiguous.
- A large, stable Home action is the only routine touch navigation. Returning Home does not stop
  playback.
- Touch transport is absent on RH1; Play/Pause and skipping remain physical.

### Hardware and light

- Previous / Next, encoder press and rotation are central, eyes-free controls with identical meaning
  across AQENO.
- Recognition feedback may be slightly more explicit than in other models: one short low-intensity
  light response after a physical intention, paired with visible or audible feedback when policy
  allows. It is never a decorative colour show.
- Night and `OFF` suppress all user-facing light.

### Display states and accessibility

- `INTERACTIVE`: artwork selection or artwork-dominant Now Playing.
- `DIM`: artwork only, or artwork plus one state mark if testing proves it useful; no controls.
- `OFF`: no pixels or light. Physical playback remains usable.
- Large forgiving targets, no reading prerequisite, no precision gesture, no timed response and
  stable spatial placement are baseline requirements.
- Errors preserve context and use a familiar symbol or short sound; they do not open technical
  dialogs.

### Growth path

Kids Early establishes durable spatial and physical habits: artwork selects, the centre control
plays/pauses, outer controls move through the current work and one stable action returns Home. Kids
Reading must preserve those anchors.

## Concept B — Kids Reading

### Mental model and hierarchy

**“I recognise my content and can use its name to find more.”** Artwork remains the primary anchor;
short language makes identity, series and progress more precise. Hierarchy is artwork, title, short
context and current state.

### Navigation, Home and content selection

- Home preserves the familiar artwork positions and direct-tap playback path where practical.
- Two or three covers gain short labels; the label never replaces recognisable artwork.
- When real content volume requires it, an explicitly named collection can open one shallow grid.
  This depends on the existing `Collection` concept becoming implemented; presentation must not
  fabricate groupings from filenames.
- No search, keyboard or provider navigation is assumed. A visible, stable return action replaces
  hidden gestures.
- Resume is shown as a property of a work, not as a separate “continue” application.

### Now Playing

- Artwork remains large but shares the frame with title and one useful line such as chapter name or
  `Chapter 5 of 12`.
- A restrained progress indicator is useful when the content is seekable; it need not be draggable.
- Home remains the one touch navigation action. Transport remains physical on RH1.

### Hardware and light

- Physical semantics are unchanged and remain primary for routine listening.
- Light acknowledgement can be as explicit as Kids Early during the transition, then become more
  restrained by preference. Meaning is never colour-only.

### Display states and accessibility

- `INTERACTIVE`: labelled artwork selection or artwork + title + chapter Now Playing.
- `DIM`: smaller artwork, title and at most one chapter/context line.
- `OFF`: no visible output.
- Short labels use readable line lengths and predictable truncation. Navigation never requires fast
  reading, precise drag or remembering a hidden hierarchy.

### Growth path from Kids Early

The transition changes one learned dimension at a time:

1. preserve the same artwork positions, tap behaviour, Home action and physical controls;
2. add the spoken/written title beneath familiar artwork without adding a navigation level;
3. add a short playback context such as chapter only where the domain provides it;
4. introduce one visible collection entry only when the real library no longer fits direct choice;
5. retain a direct familiar-content path so growing complexity never blocks the old route.

Progression is manually selected and reversible. AQENO may later suggest a change, but it must not
silently infer reading competence or readiness. Kids Explorer remains a documented future discovery
stage, not part of this four-concept decision.

## Concept C — Adult / Kitchen

### Mental model and hierarchy

**“Show me what is relevant now and let me resume or switch quickly.”** Recognition still matters,
but compact context supports scanning while hands or attention are occupied. Hierarchy is resumable
current content, recent relevant works, title/context and progress.

### Navigation, Home and content selection

- Home may combine one prominent resume opportunity with a compact list of available content.
- A “Continue listening” presentation is supported only by existing per-profile resume data; a
  ranked or curated section would require an application query and product rule not yet present.
- Rows may show artwork, title and one context line. Touch targets remain forgiving even when visual
  density increases.
- Content kinds such as audiobook, podcast or live stream may influence useful metadata and
  transport behaviour. They do not become apps or provider tabs.
- Radio stations, podcast feeds and recent-use ordering are valid UX hypotheses, not current
  ingestion/discovery commitments. Favourites are excluded until their domain meaning is decided.
- Navigation may use one shallow content grouping when backed by implemented Collections. Search and
  free text remain outside the appliance UI.

### Now Playing

- Artwork and title remain primary, with episode/chapter, elapsed/remaining time and progress shown
  only when accurate and useful for the content kind.
- Live content does not pretend to have seek progress or resume.
- Home/back-to-content is clear. Routine transport remains physical; touch may expose a single
  contextual action only when the content requires one and the capability exists.

### Hardware and light

- The encoder is the dominant kitchen control: fast volume and play/pause without wet hands needing
  the screen. Previous / Next retain their content-kind semantics.
- Light feedback is normally briefer and dimmer than in Kids Early; interaction acknowledgement or
  a wait that needs explanation are the only reasons to illuminate it.

### Display states and accessibility

- `INTERACTIVE`: one resume opportunity plus compact scannable content, or information-rich Now
  Playing.
- `DIM`: artwork, title and one useful content/context line; a source/provider label appears only if
  it is meaningful to the person, not technical status.
- `OFF`: no clock or status. A clock requires explicit `AMBIENT` authority.
- The model supports quick glances and one-handed taps, but its denser list scanning creates more
  visual and cognitive demand than the other concepts.

### Growth path

This is not the automatic destination of Kids Reading. If chosen later, familiar artwork, direct
selection, physical semantics and Now Playing hierarchy remain intact while the Home surface shifts
from bounded recognition to scanning and resume-oriented context.

## Concept D — Accessible / reduced complexity

### Mental model and hierarchy

**“I can always identify the current state and one safe next action.”** This is a voluntarily chosen
reduced-complexity interaction model, not an age label and not Adult UI at 150%. Hierarchy is current
state, one primary action, then at most one or two alternative content choices.

### Navigation, Home and content selection

- Home presents one dominant action such as resuming the current work, followed by no more than two
  large labelled content choices that actually exist.
- A vertical action layout can provide full-width targets and stable reading order without a dense
  grid. Artwork accompanies labels when it improves recognition.
- No nested navigation is the target. If content volume makes that impossible, one shallow screen
  with an always-visible return action is the maximum hypothesis to test.
- No swipe, drag, long press, timeout, hover-only affordance or colour-only choice.
- “Message” is not shown unless a future message capability is designed and available.

### Now Playing

- Large artwork is paired with a large title and an explicit plain-language state such as “Playing”
  or “Paused”.
- Progress is secondary and appears only if it helps orientation; precise time is not assumed useful.
- One very large Home action has stable placement. An optional large touch Play/Pause control is a
  legitimate accessibility hypothesis because redundant input paths can be valuable here, but it is
  not authorised until tested as a concrete capability.

### Hardware and light

- Physical controls may be the primary interface. Their semantics never change between models.
- Feedback should be longer or higher contrast only where perception testing supports it, while
  staying calm. Every light meaning also has shape, state, sound or physical-action context.
- Night and `OFF` always override feedback.

### Display states and accessibility

- `INTERACTIVE`: explicit state plus one dominant action and at most two alternatives.
- `DIM`: very large title or artwork and an unambiguous playing/paused state; no action controls.
- `OFF`: no visible output; physical controls remain active.
- Large targets, strong contrast, scalable text, visible focus, stable placement, generous error
  tolerance and recoverable taps are structural. No demographic assumption is encoded.

### Growth path

This model is selected or left according to preference and need. It is not a lower stage. Moving to
or from another model preserves content identity, resume, hardware semantics, artwork language and
the stable return path.

## Cross-profile matrix

`Low / medium / high` describe the intended interaction, not a person's ability.

| Dimension | Kids Early | Kids Reading | Adult / Kitchen | Accessible |
|---|---|---|---|---|
| primary recognition anchor | artwork / token | artwork + short label | artwork + contextual text | explicit state + artwork/label |
| simultaneous primary choices | 2–3 | 2–3 | 3–6 scannable rows/choices | 1 dominant + up to 2 alternatives |
| text dependence | none / very low | low–medium | medium–high | medium, plain and large |
| list use | none | optional shallow grid | compact list is central | avoided |
| navigation depth target | direct | direct + at most 1 | up to 2 shallow levels as needed | direct + at most 1 |
| artwork prominence | dominant | dominant | supporting/strong | supporting/strong |
| touch role | direct content selection | selection + shallow browse | scanning and switching | large explicit actions |
| physical-control role | central | central | central, eyes-free | potentially primary |
| touch transport on RH1 | no | no | normally no | testable redundant path only |
| Now Playing density | very low | low–medium | medium–high | low and explicit |
| DIM priority | recognisable artwork | artwork + identity | glanceable context | unmistakable state |
| precision required | very low | very low | low | minimal |
| main cognitive operation | recognise | recognise + read | scan + compare | confirm one safe action |

## Shared primitives versus distinct patterns

### Necessary shared AQENO primitives

These are concrete enough to share without creating a universal UI engine:

- artwork surface with consistent crop, fallback and selected/current states;
- title and optional one-line context text styles;
- large action and stable Home/return action;
- playback-state mark and non-draggable progress presentation;
- focus, pressed, unavailable-content and calm-failure treatments;
- exact 800 × 480 spacing, colour, typography, radius and motion tokens;
- display-state container that can present profile-specific `INTERACTIVE` and `DIM` content while
  preserving authoritative `OFF`;
- semantic physical-input and LED-feedback presentation hooks.

### Differences not ready for abstraction

- fixed artwork field versus labelled grid versus compact list versus dominant-action stack;
- whether Home begins with content, resume or an explicit action;
- information selection and ordering in each Now Playing composition;
- whether accessible redundancy justifies touch Play/Pause;
- number and meaning of content-browsing levels;
- model selection, transition and suggestion policy.

Do not introduce a renderer strategy, layout DSL, JSON UI definition, universal tile system or
target-group engine from these sketches. First test the compositions; extract only repeated code
that survives those tests.

## Domain and capability gaps

| Idea | Current support | Gap before it may become UI |
|---|---|---|
| direct content artwork selection | implemented in Kids Early | none for current slice |
| resume a selected work | implemented per `(ContentItem, Profile)` | presentation decision only |
| ranked “Continue Listening” section | resume data exists | recency/query and ordering product rule |
| chapter/title context | content/chapter model exists | expose the required view-model fields |
| content grouping | `Collection` documented | persistence/application behaviour and a concrete use case |
| radio/podcast playback | kinds/sources anticipated | ingestion, discovery and current capability availability |
| model choice/transition | `ExperienceLevel` exists | explicit selection authority and UX; no management flow yet |
| accessible touch transport | semantic action exists | concrete need, capability rule and user validation |

Future-feature gaps remain favourites, personal messages/Bherz, Send to AQENO, remote delivery,
general search and Ambient content. None appears in a current preview, even as a disabled control.

## Complexity risks

1. Four copied QML trees would turn concepts into product forks and make state behaviour diverge.
2. A premature universal renderer would encode guessed commonality and make good compositions harder.
3. Calling content types “modes” would recreate an app launcher.
4. Deriving model selection from age would stereotype users and silently change learned behaviour.
5. Making physical buttons navigate in one model and transport in another would destroy muscle
   memory and complicate semantic input.
6. Dense Adult content could smuggle provider/source architecture into the Device UI.
7. Accessible redundancy could become permanent control clutter without concrete validation.
8. Profile-specific DIM implementations could accidentally weaken authoritative `OFF` or Night.
9. Visual previews could imply capabilities that the Core cannot currently deliver.

## Visual briefs

All previews are rendered at exactly 800 × 480 without operating-system chrome. They use the same
dark, warm AQENO palette, type family, radius system, artwork treatment and restrained motion. SVG is
preferred for interface graphics. Previews are design exploration, not implementation specifications.

### Kids Early preview set

This set contains three preview frames but deliberately only two navigation surfaces. Inventing a
detail screen merely to make Home and content selection different would make the interaction worse.

**Home / entry:** Two-choice and three-choice variants. Two or three square artworks,
approximately 220–250 px each, centred with generous unused space. No required labels; stable current
mark. Each artwork is the entire touch target. No header, categories, page dots, settings or transport.

**Content Selection frame:** Home itself is the selection model. Show the same composition during a
recognised press with restrained scale/outline feedback immediately before Now Playing. It is a
separate exploration frame, not a third destination. Any later separate selection surface must
demonstrate a real problem that Home cannot solve and must not invent a library hierarchy.

**Now Playing:** Artwork approximately 360–400 px high, centred or slightly offset; one 84 px Home
action at a stable edge; optional simple playing/paused mark. No timecode, chapter text, source,
touch transport or decorative animation. Mood: safe, immediate, quiet and tactile.

**DIM:** Artwork alone at reduced size and brightness. No buttons or moving progress.

### Kids Reading preview set

**Home:** The same two/three artwork anchors as Kids Early, now with one short label beneath each.
Artwork approximately 190–220 px; labels use at most two lines. No category rail or app tabs.

**Content Selection:** One shallow labelled grid only as an explicit Collection experiment: three
large covers per row, clear title, persistent 72–84 px return action. No search or nested categories.

**Now Playing:** Artwork approximately 300–340 px high on the left; title and one chapter/context line
on the right; restrained non-draggable progress; 84 px Home action. No touch transport or metadata
wall. Mood: familiar, encouraging and never school-like.

**DIM:** 140–180 px artwork, title and one chapter line; no navigation.

### Adult / Kitchen preview set

**Home:** One prominent resumable work occupying roughly the upper 45%, followed by three or four
compact content rows. Each row has 88–104 px artwork, title and one useful context line with a touch
target at least 72 px high. No greeting required, no provider tabs, app icons or technical status.

**Content Selection:** A scannable single list or one Collection level with 80–96 px artwork, title
and episode/chapter/kind context where useful. Stable return action; no keyboard or dense toolbar.

**Now Playing:** Artwork approximately 280–320 px high; title, episode/chapter, accurate progress and
time context when seekable. Home/return is clear; transport remains physical. No waveform, equaliser,
queue editor or source diagnostics. Mood: composed, fast to scan and domestic rather than app-like.

**DIM:** 120–160 px artwork, title and one context line. No clock unless the separately authorised
state is `AMBIENT`.

### Accessible preview set

**Home:** One full-width dominant action 120–150 px high, followed by up to two 96–120 px choices.
Large icon/artwork plus plain label, strong focus boundary and stable placement. No dense grid,
gesture hint, tiny secondary link or age-coded aesthetic.

**Content Selection:** At most three large rows, each at least 104 px high, with artwork, large label
and generous spacing. One persistent 84–96 px return action. Avoid scrolling in the primary test.

**Now Playing:** Artwork approximately 240–300 px, large title and explicit `Playing` / `Paused`
state. One 96 px Home action. A 96 px touch Play/Pause variant may be compared against physical-only
control, clearly labelled as an accessibility experiment. No precise timecode requirement or crowded
secondary controls. Mood: dignified, calm, unambiguous and high-quality.

**DIM:** One very large title or artwork plus explicit state; no touch action.

## Comparative evaluation

| Criterion | Kids Early | Kids Reading | Adult / Kitchen | Accessible |
|---|---|---|---|---|
| learnability | very high for bounded content | high; builds on Early | medium; familiar scanning but more choices | very high if labels are understood |
| recognition | very high | very high | medium–high | high |
| motor accessibility | high | high | medium–high | very high target |
| cognitive load | very low | low | medium | very low |
| glanceability | high through artwork | high | high through context | very high through explicit state |
| hardware synergy | very high | very high | very high for distracted use | potentially highest |
| growth continuity | baseline | strongest link from Early | preserves anchors, larger navigation shift | preserves anchors, deliberately separate path |
| AQENO consistency | high | high | must resist app/list conventions | must resist clinical styling |
| software complexity cost | low/current | medium | high | medium–high until redundancy is tested |

These are hypotheses for prototype comparison, not scored evidence.

## Recommended next design iteration

1. Produce low-fidelity 800 × 480 previews for all four sets using identical AQENO visual tokens and
   representative existing content; mark every unimplemented capability directly in design notes,
   not on the rendered device screen.
2. Compare two versus three choices for Kids Early and preserve the winning spatial anchors in Kids
   Reading.
3. Prototype the Kids Early → Kids Reading progression as a sequence, not two unrelated galleries.
4. Compare Adult Home with and without a resume-first block using only data AQENO already owns.
5. Compare physical-only versus deliberately redundant touch Play/Pause for Accessible Now Playing.
6. Test each set against learnability, recognition, motor demand, cognitive load, glanceability,
   hardware synergy, growth, consistency and implementation cost.
7. Select the smallest set of interaction models that produces materially better use before
   designing any shared architecture or committing implementation scope.
