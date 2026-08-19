# AQENO Player — Product Foundation

**Status:** v0.2  
**Date:** 2026-08-17  
**Purpose:** Product foundation and decision frame for discovery and implementation.

## 0. Why AQENO exists

**Canonical statement of project motivation. Decided in ADR 0015; this section is its home.**

> **AQENO is built to be excellent, not to justify a business.**

AQENO is being built because we want an exceptionally good audio player made to our own design. The
first one is for a specific child in the maintainer's family, who will use it every day. That is the
real requirement AQENO answers, and it does not have to be defended against any existing product.

The guiding sentences, in the order they matter:

> **The first AQENO is built for real use, not for a hypothetical market.**
>
> **The primary design case starts with a child, but AQENO's design horizon is broader.**
>
> **Existing products are benchmarks and sources of learning, not reasons for AQENO not to exist.**
>
> **A feature does not need to be unique. It needs to make AQENO better.**
>
> **Optimal does not mean maximal.**
>
> **Use technology where it removes friction, not where it adds features.**
>
> **Commercialization is an option earned by a good product, not a requirement imposed on its
> development.**

And the question every product decision answers first:

> **Does this make AQENO meaningfully better for the person using it?**

There is no obligation to innovate. CD players, MP3 players, radios and telephones existed in large
numbers with nearly identical core functions; they earned their place through handling, design, build
quality, reliability, feel, price, scope, integration and preference. A capability existing elsewhere
is not a reason to leave it out — and not a reason to include it either. The decision order in
`AGENTS.md` § "Deciding what to build" applies.

## 1. Purpose and identity

**Canonical product identity. Decided in ADR 0023.**

> **AQENO is a calm everyday companion for audio, time and personal connection.**

AQENO is an **open, adaptive, audio-first platform** that makes digital audio understandable through
calm, physical interaction while preserving freedom of hardware, content and interaction. Audio is
the primary pillar. Time and personal connection are the other two, and they are part of the
product rather than additions to it.

> **AQENO adapts to people — people should not have to adapt to the player.**

Depending on user and configuration, one AQENO may be an audio, audiobook, music or podcast player,
an internet radio, a clock, an alarm clock, a modern radio alarm, a visual timer, a routine helper,
or the recipient of selected personal content and messages.

**The three pillars are the first test for any capability:**

> **AUDIO · TIME · PERSONAL CONNECTION**

A capability that supports none of them is out of scope, whatever else can be said for it. One that
supports a pillar still has to pass the decision order in `AGENTS.md` § "Deciding what to build".

**AQENO is not** a smartphone, tablet, smart display, Alexa/Google-Home-class smart speaker, game
platform, social device, news portal or general information dashboard. There is no development
toward a news feed, weather dashboard, browser, app store, games, social feed, advertising,
engagement mechanics or arbitrary notifications.

Time and personal connection are identity, not schedule: clock, alarm, timer and `Send to AQENO`
remain future work under ADR 0023 § 6 and ADR 0025 § 3, with no surface on the device today.

The first product focus is **AQENO Kids**, but children do not define the platform. The same core
should serve adults, families and people who benefit from reduced interaction complexity, including
older people and people with motor, cognitive or other disabilities. These are use contexts of one
product, not reasons to create separate Kids, Senior or Accessibility codebases.

## 2. Product position

> **The independence of a Toniebox with the freedom of a tablet — without turning an audio player into a tablet.**

AQENO sits between intuitive but closed audio systems and flexible but distracting general-purpose devices.

- Audio-first, not screen-first.
- Open content, not proprietary media objects.
- Adaptive interaction, not a fixed age-specific UI.
- Physical-first, display-assisted, touch-optional: everyday use never requires touching the screen
  (ADR 0024).
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
High-frequency actions work through physical controls and muscle memory, without screen navigation.
Since ADR 0024 this extends to navigation itself: no function, and no path to a function, may
require touching the panel. Touch remains available and welcome; it is never the only way.

### P07 — Screen when useful, screenless when possible
The display adds orientation, artwork, status, selection, feedback and — later — time, timer and
alarm presentation. It is not required for fundamental playback actions, and its presence, size and
technology are a platform capability rather than a product dependency (ADR 0025).

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

Automatic reduction during active playback is not Ambient. AQENO may recede from a complete
interactive surface through a short glanceable `DIM` presentation to `OFF`; this is playback context,
not an idle display mode. With no playback and no interaction, the default remains `OFF`.

### P15 — Show capability, never absence
AQENO presents only functions that are currently usable on the device. An unavailable optional
capability has no device UI surface; it is not shown disabled, locked, badged or as an upgrade
prompt. The local Core must feel complete rather than like a restricted tier.

### P16 — Appliance simplicity
The Device UI exposes few concepts, shallow navigation, one clear contextual action and immediate
understandable feedback. Physical controls carry frequent actions; the display does not imitate a
tablet or expose technical structure. Detailed rules and the mandatory design-review questions live
in `docs/product/DEVICE_UI_PRINCIPLES.md`. Presentation translates technical state into human
meaning: a heart rather than an unread-message counter, or seamless resume rather than persistence
status.

### P17 — Accessibility through simplicity
AQENO starts with large and forgiving controls, little required text, shallow navigation, immediate
feedback and no mandatory precision gesture or routine smartphone use. Concrete accessibility needs
may require further work, but they refine shared capabilities rather than defaulting to labelled or
stigmatising special modes.

### P18 — Repairable by intent
AQENO should remain useful beyond the life of an individual electronic component. Hardware choices
favour access, identification, repair and functionally compatible replacement without turning the
device into a speculative modular platform.

> **AQENO is assembled, not sealed.**

### P19 — AQENO does not compete for attention
**ADR 0023.** Smart, in AQENO, means the device takes work off a person — not that it creates as
many interactions as possible. AQENO may present information and may draw attention to a genuinely
relevant event. It may not pursue attention: no engagement loops, artificial badges, unnecessary
animation, permanently changing content, recommendations that exist to raise usage time, "discover
more" mechanics or unnecessary notifications. When AQENO is not needed, it recedes visually and
acoustically. P12 forbids the mechanics; this principle states the posture they follow from.

### P20 — Physical feedback before artificial feedback
**ADR 0024.** Prefer inherent physical feedback over feedback AQENO has to invent. An encoder should
have felt detents, a button or rocker a defined actuation point; the hand should know what happened
before the screen says so. Do not emit a sound for every physical action by default. Where the
result of an action is itself unambiguous — the volume changes, audio starts, the focus ring moves —
that result is the feedback, and adding a second layer on top makes the device noisier, not clearer.

### P21 — Everything essential works without looking
**ADR 0026.** Every essential everyday action is performable blind. A control that can only be used
by reading a label, seeing a screen or watching an indicator fails this principle, whatever else it
does well. This is the principle the dark-room requirement, the permanent control meanings and the
illumination rules all serve.

### P22 — Controls are identified by hand
**ADR 0026.** Controls with different semantic roles are distinguishable by touch — through position,
geometry or texture — without light and without labels, and their spatial relationship is preserved
across AQENO hardware variants. Muscle memory built on one AQENO transfers to the next.

### P23 — Accessibility without looking accessible
**ADR 0026.** AQENO is meant to be used intuitively by children, adults, older people and people with
motor or visual limitations — and must not look like a children's toy, a senior device or a medical
aid. Accessibility is part of ordinary good industrial design, not a special edition. There is one
AQENO interaction model; there is no separate Kids, Adult, Senior or Accessible operating logic.
Mechanical adaptation such as larger or grippier caps is welcome and changes neither electronics nor
interaction logic.

### P24 — Light assists, it never defines
**ADR 0026.** Illumination supports operation and never constitutes it: every control must be
findable and operable with all light off. Control light is contextual guidance, not permanent status
display. **DARK means zero visible light** — no display, no control LED, no status LED, no glowing
key, no unavoidable operating indicator. No hardware may force visible residual light.

### P25 — Silence is the default
**ADR 0027.** Sound must earn its presence. AQENO makes a sound only where it supports eyes-free
operation, confirms a relevant action, signals a relevant event or needs timely attention — never
because an input was recognised. No tone for an encoder detent or an ordinary button press;
mechanical feedback stays primary (P20). Every AQENO sound belongs to one of four classes —
`FEEDBACK`, `NOTIFICATION`, `ATTENTION`, `ALARM` — and that class, not the feature, decides whether
it may be heard. **Dark is not mute and Night is not a master mute:** an alarm may sound with the
panel completely black, while a message arriving at night makes no sound at all.

## 4. Adaptive experience

AQENO should use a shared capability model rather than separate rigid products for each age,
ability or setting. `Kids Early`, `Easy` and `Standard` describe experience configurations; they are
not separate cores or claims that one configuration satisfies every person in a demographic group.

| Stage / mode | Primary UI | Typical navigation | Screen role |
|---|---|---|---|
| Kids Early | Images, minimal/no text | NFC + physical controls | Optional/discovery |
| Kids Reader | Images + labels | NFC + touch | Selection and learning |
| Kids Explorer | Library, categories, search | Touch + NFC | Primary discovery surface |
| Easy | Large tiles + large text | Touch + physical controls | Simple contextual surface |
| Standard | Full library UI | Touch + controls | Full interface |

Transitions remain manually controllable. AQENO may suggest a different complexity level but must not silently decide that a child or other user is ready for it.

Needs should be modelled directly where they become real: larger targets, reduced navigation,
audio feedback, volume boundaries or alternative input. Do not introduce a generic persona, theme,
“senior mode” or “disability mode” in anticipation.

## 5. Physical interaction

> **Frequent actions are physical. Contextual actions are visual.**

> **tactile first · illumination assisted · display enhanced · touch optional** (ADR 0026).

Control set — five controls, each with one permanent role (ADR 0026 § 2):

| Control | Rotation | Short press | Reason |
|---|---|---|---|
| **SELECT** rotary encoder | move focus / change a value | activate, confirm | eyes-free selection without a panel |
| **PREVIOUS** | — | previous item in content order | one direction, one meaning |
| **NEXT** | — | next item in content order | one direction, one meaning |
| **VOLUME** rotary encoder | volume down / up | play / pause | the two most frequent actions, always in the same place |
| **HOME** | — | back to the familiar starting point | one reliable way out, from anywhere |
| Touchscreen | — | optional convenience for the same actions | never the only path |
| NFC | — | content/action shortcut | physical, intuitive, optional |

> **Volume stays volume. Play/Pause stays Play/Pause.**
>
> **PREVIOUS and NEXT are content order. HOME is the way out.**

Five tactilely findable positions whose spatial relationship is invariant across AQENO hardware:

```text
    SELECT      PREV   NEXT      VOLUME
      ( )         <      >         ( )

                  HOME
```

**Every control means one thing in every state.** Eyes-free operation depends on it, which is why
ADR 0026 withdrew ADR 0024's context-resolved LEFT/RIGHT: a person who cannot see the screen cannot
know which context they are in, so they cannot know what a context-dependent control will do.

PREVIOUS and NEXT move within the current content's order — track, chapter, section, image — as
ADR 0009 § 2 defines per kind. They are never UI navigation and never move focus, not even in a
menu. Hold-to-seek and every other timed or repeated gesture are excluded.

HOME always leads to the familiar AQENO starting point, never stops playback, and resolves an
interruptive state. It is not a configurable everyday key and carries no second function. Whether
AQENO also needs a separate BACK control is deliberately open: the current hypothesis is that a
shallow information architecture makes one unnecessary, and that must be proved in real use rather
than assumed.

> **Normal everyday AQENO operation must not require long-press or double-press gestures.**

Long press stays technically available for setup, service and hardware cases. It is not part of any
everyday path, and no default binds it. There is no separate OK button, and no dedicated Favourite
or Menu button is added unless testing proves one necessary.

On RH1, PREVIOUS, NEXT and HOME are existing Cherry MX switches; the target device may replace
PREVIOUS and NEXT with one quality momentary centre-off rocker. That is a construction change, not a
semantic one.

**An ordinary one-handed press must not appreciably move AQENO on a normal surface.** How that is
achieved — rubber feet, mass, centre of gravity, enclosure geometry, actuation force — is a
mechanical decision, so controls may also sit on a well-reachable inclined front face. This replaces
the earlier rule that controls had to be on the top or an upper surface. Enclosure design itself
remains out of scope.

RH1's assembled Cherry MX and Qwiic controls are prototype input hardware. They exercise the same
semantic boundary and define nothing about the target layout (ADR 0024 § 4).

What each control does in each situation is normative in
`docs/implementation/INTERACTION_MATRIX.md`.

### Rotary controls

Rotary controls are specified abstractly (ADR 0026 § 7): incremental encoder, integrated push,
clearly felt detents, consistent direction, and a rotational and push force usable by a child and by
a person with reduced hand strength. A standardised shaft — 6 mm is the current preference — keeps
caps exchangeable, so the same electronics can carry compact, standard or easy-grip ergonomics.
SELECT and VOLUME should be the same part with different caps, distinguishable by hand through rim
structure, profile or knurling, without either looking like a special aid.

Maker breakout boards are one implementation of that contract and never its definition.

Core actions must not depend on precise dragging, swiping, double taps, long presses, tightly packed
controls or short response windows — not even with an alternative path available. A touchscreen can extend AQENO, but physical controls
and tokens are a first-class access path for children and adults alike.

## 6. Dark-room requirement

> **AQENO must be usable in a completely dark bedroom without requiring the display or any light to turn on.**

This is a core product requirement, not an energy-saving feature.

During bedtime playback AQENO must be able to:

- turn the display fully off while audio continues;
- turn off decorative and status LEDs — **DARK means zero visible light**, including a glowing
  control or key and any unavoidable operating indicator (P24);
- suppress system sounds and visual flashes;
- keep volume and play/pause physically operable;
- apply a configurable night-time volume ceiling;
- optionally apply a sleep timer or bedtime scene;
- remain dark when a physical playback control is used.

Playback state and visual state are separate architectural concepts.

### Display-state model

AQENO treats the display as an explicit state machine rather than a generic always-on UI surface:

- **OFF** — panel dark; no visual activity;
- **DIM** — glanceable, deliberately reduced information where explicitly useful; not merely the
  interactive view at lower brightness;
- **INTERACTIVE** — active touch/navigation interface;
- **AMBIENT** — deliberately enabled passive visual mode such as selected photos or artwork;
- **SETUP** — bounded on-device pairing, onboarding and recovery; not general administration.

For **Kids Early**, active playback may recede progressively after visual interaction:
`INTERACTIVE → DIM → OFF`. The `DIM` stage is short, glanceable Now Playing information without
visible controls, navigation or attention-seeking animation. It is skipped while Night/Bedtime policy
is active. Playback changes, buffering and chapter transitions do not wake the display unless the
user explicitly requests visual interaction.

`AMBIENT` is not a fallback for inactivity. It is a scene/capability that must be intentionally enabled.

> **The AQENO display should recede, not simply turn off:** `INTERACTIVE` means interact, `DIM`
> means glance, and `OFF` means disappear.

## 7. Open physical media and NFC

AQENO preserves the haptic strength of physical media without requiring proprietary figures. NFC is
an open shortcut layer, not the content store or a toy-only interaction model.

- A tag may identify an item, collection, profile, scene or action.
- Tags may live in 3D-printed figures, cards, wooden tokens, stickers, key rings or existing toys.
- AQENO treats compatible tags by identifier, not by the object's brand or original product type.
- A tag launches only an AQENO-local assignment to content or an Action already available to AQENO.
  Recognition never authorises acquisition, extraction or decryption from another content system.
- **Place, do not aim.** The device offers a generous, flat object area rather than a target to hit.
  It has **no recess and no well** (ADR 0026 § 11): standing figures must work, simple 3D-printed
  objects must need no AQENO-specific under-geometry, and flat cards must work equally. The
  enclosure reserves that area from the start; the antenna solution is a later measurement.
  Magnetic positioning may be added later as an option — NFC identifies, magnetism may position —
  but never as a precondition, and never as mandatory proprietary geometry.
- AQENO can publish reference dimensions and printable holders for commodity NFC tags.
- The same object may evolve with the user: one story at age three, a collection/category later.
- NFC remains optional; the library never depends on owning physical tokens.
- Named third-party compatibility or integration is a separate product/legal decision, not implied
  by technically reading a compatible tag.

A story figure, jazz card, radio card or large distinctly shaped token all express the same product
principle: an understandable physical object can represent an action. The domain does not infer an
age group, brand or object category from that assignment.

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

## 10. Management and assistance model

Use roles rather than hard-coded parent/child relationships:

- **User** — consumes and controls permitted content.
- **Manager** — curates content and experience boundaries.
- **Owner** — controls device/account ownership and management rights.

This supports parent → child, an independent Owner/User and an authorised family member assisting
another adult without encoding those relationships as core roles.

A listening **Profile** is separate from these management roles. It is a local context for media,
favorites, progress and presentation—not a login, account or authentication identity. Shared
content is the default; managers can curate inherited groups and cheap per-medium exceptions.
Every entry path respects the active profile's effective access, and unavailable content is absent
instead of appearing locked. Management authorization never derives from the selected profile
(ADR 0019).

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

The first concrete platform is **AQENO Reference Hardware 1**, documented in
`docs/hardware/HARDWARE_REFERENCE.md`. It proves the ports and product experience; it does not define
which controls, buses, board or display every AQENO device must have.

- slim core player;
- USB-C power;
- ordinary external power bank is a valid mobile-power option;
- no proprietary battery requirement;
- initial reference display: approximately 5–7 inch touch;
- two rotary encoders (SELECT, VOLUME) plus PREVIOUS, NEXT and HOME;
- no everyday power button on the primary control surface: AQENO distinguishes `ACTIVE`, `SLEEP`
  (display dark, instantly usable) and a deliberate `OFF`, and any ordinary interaction leaves
  `SLEEP`. A genuine shutdown control belongs away from the primary surface or in local
  administration; cutting board power is not a product definition of `OFF` (ADR 0026 § 8);
- optional NFC;
- optional ambient-light and near-hand proximity sensing, used for adaptive brightness and for
  temporary orientation in a dark room — never for gesture control, and never required for
  operation (ADR 0026 § 10);
- standard/replaceable audio components where practical;
- simple printable enclosure designs.

The RH1 touchscreen is used for the current Device UI work, but a touchscreen is not a prerequisite
for understanding or operating core playback. A future device may rely on a speaker, encoder, a few
large controls, tokens and restrained feedback, provided its adapters express the same relevant user
intentions.

A future product may integrate prototype modules for manufacturing efficiency; the repairability
rules below govern that trade-off rather than hypothetical series cost alone.

### Repairability, longevity and standard components

AQENO should look and feel like a finished product without hiding its construction from the person
who maintains it:

> **Product outside. Understandable hardware inside.**

The canonical hardware principles are:

- **Replacing a component should not require replacing the device.** Where technically and
  economically reasonable, likely wear, failure and platform-change points remain independently
  accessible and replaceable. This includes compute hardware, display, speakers, amplifier,
  controls, NFC, sensors and power components as categories—not a requirement to design modules for
  all of them today.
- **Standard components should remain standard components.** Commodity parts should stay
  functionally replaceable by freely obtainable compatible parts where that creates no material
  product disadvantage. AQENO does not turn an ordinary speaker, switch, sensor or connector into an
  artificial proprietary spare.
- **Replaceability is more important than permanent part identity.** A successor part may require a
  different adapter, cable set or mounting solution. Exact long-term availability of one part number
  is not assumed; preserving the rest of the device matters more.
- **The enclosure should outlive individual electronics.** Future mechanical decisions should allow
  for compute, display, sensor and audio electronics changing on shorter cycles than a sound product
  form. This principle does not define a mechanical platform, interface or enclosure architecture.
- **Repairability first. Upgradeability where it comes naturally.** A repairable boundary may permit
  a better later component, but AQENO does not become a PC-like upgrade platform and does not design
  upgrade paths without a real need.
- **Modularity serves longevity, not complexity.** Separation is justified when it improves repair,
  replacement availability, likely component change or reuse. It is not a reason for cartridges,
  adapters, mechanical standards or plugin mechanisms for every part.
- **Integration may reduce cost, but should not intentionally create unnecessary irreparability.** A
  later product may integrate today's prototype modules where that genuinely reduces cost and
  complexity. Hypothetical series cost does not shape Reference hardware today, and integration must
  still be weighed against repair and useful life.
- **Hardware should be identifiable.** AQENO should be able to record the installed component type,
  relevant electrical characteristics, connection method, hardware revision and known compatible
  replacements. This establishes the information requirement; it does not require a service manual
  before hardware exists.

Repair should be easier and cheaper than replacing the whole device when that is technically and
economically reasonable. Repair quality is assessed through total effort as well as purchase
price—tools, part availability, specialist knowledge and the risk of damaging otherwise functional
components all matter.

Replaceability does not silently broaden the support promise: `Reference`, `Compatible` and
`Community` retain their meanings. A functionally suitable substitute may be repairable without
becoming an officially tested AQENO component.

No artificial spare-part lock is introduced without a technical reason: avoid unnecessarily
proprietary connectors or fasteners, serial-number binding, replacement-part pairing and software
blocks on compatible parts. AQENO likewise introduces no hardware-generation dependency, cloud
service or expiry mechanism whose primary purpose is to make functioning hardware unusable.

Service-relevant electronics should prefer suitable removable connections and fasteners over
permanent bonding. This is not a ban on adhesive: the test is whether a realistic repair becomes
needlessly destructive.

These principles guide rather than override engineering reality. Safety, electrical reliability,
acoustics, mechanical stability, size, cost, regulation and manufacturability may justify a less
repairable choice. Such a trade-off should be explicit rather than an accidental result of
convenience.

For AQENO, sustainability begins with useful life: repair, compatible replacement, continued
software support, reuse of functioning parts and avoiding whole-device electronic waste. Material
choice and recyclability remain relevant, but they do not substitute for keeping the device usable.

`P07 Screen when useful, screenless when possible` and ADR 0017 apply the same discipline to the
display: it is a replaceable capability rather than the identity or prerequisite of the audio
device. This does not imply a generic hardware-capability framework for every component.

## 13. Capabilities worth having

These are capabilities we want AQENO to have because they make it better to use — not claims of
differentiation. Several of them are commodity in this product category, and that is not an argument
against them (ADR 0015 § 2). Each still has to earn its place when it is actually built.

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

## 14. Use contexts, not product forks

The current names are discovery shorthand, not commitments to separate editions:

- **Kids** — autonomous and increasingly capable audio use from early childhood onward;
- **independent simple audio** — radio, music, podcasts or Bluetooth in a kitchen or living room,
  without requiring a complex app or voice assistant;
- **assisted use** — a person uses AQENO independently for routine listening while an authorised
  Manager helps with configuration or content where requested;
- **family use** — shared content, physical actions and personal audio across ages.

All contexts share the player engine, content model, role model, hardware abstraction and adaptive
presentation primitives. Differences should arise from capabilities, configuration, content,
interaction and contextual presentation—not forks of the Core. The product need not look like a toy
or a clinical aid: its common aesthetic is warm, high-quality, calm and immediately understandable.

AQENO may provide modern connected audio without a permanently active microphone or cloud voice
assistant. This preserves a product option around privacy, speech accessibility and domestic calm;
it is not a competitive marketing claim and does not prohibit a future explicitly chosen input.

## 15. Business and trust boundaries

Commercialisation is optional and shapes no current decision (ADR 0015 § 6). The boundaries below are
the ones that must hold *if* it ever happens, and several of them — no advertising, no paid placement,
no locked controls — are product quality rules that stand on their own.

- Core local playback must not require a subscription.
- No advertising or paid placement in the child-facing interface.
- The device UI contains no locked controls, paid-tier badges, upgrade prompts or previews of
  unavailable functions. Unavailable capability means no UI surface.
- Any future commercial information belongs outside the device experience and outside every
  child-facing surface. Optional services extend the local product; they do not complete it.
- Optional cloud services may later finance remote sync, backups or family management. For personal
  audio, **the cloud is the courier, not the archive**: a delivered payload leaves it immediately
  (ADR 0027 § 7).
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
6. One platform can serve child, independent and assisted listening contexts without compromising
   their concrete needs.
7. Managers value remote curation more than detailed monitoring.
8. A slim USB-C player with optional commodity power bank is preferable to a permanently integrated battery for the reference DIY platform.

## 17. Next discovery work

Unscheduled ideas live in `docs/product/FUTURE_PRODUCT_CONCEPTS.md`. They preserve product options
without changing Vertical Slice scope, roadmap milestones or current architecture.

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

AQENO is not simple because one audience is assumed incapable. It is simple because good dedicated
devices should make their purpose obvious.

This foundation intentionally does **not** commit to a specific SBC, UI framework, audio engine or commercial model before user journeys and feasibility work provide sufficient evidence.
