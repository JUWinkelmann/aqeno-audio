# AQENO Device UI Blueprint

**Status:** Product/UX contract
**Date:** 2026-08-18
**Amended:** 2026-08-18 by ADR 0024 — navigation is physical; touch is optional
**Amended:** 2026-08-19 by ADR 0026 — five controls; HOME is the way out; PREVIOUS/NEXT never navigate
**Implemented:** 2026-08-19 — Home areas, Browse and the reduced Now Playing exist in QML
**Applies to:** AQENO Device UI, beginning with Kids Early on Reference Hardware 1

## Purpose and authority

This blueprint turns AQENO's existing product, display and UI principles into one coherent Device UI
direction. It does not replace the authority order in `AGENTS.md` and does not authorise a feature,
domain concept or management surface that the current milestone does not already require.

The UI concept preview reviewed on 2026-08-18 is a visual study, not an implementation reference.
AQENO takes its calm dark surface, strong artwork hierarchy, generous space, clear physical controls
and dedicated-device character. Layout, navigation and visible capabilities remain governed by the
repository contracts.

Five shorthand principles describe the direction:

> **Physical-first, display-assisted, touch-optional.**
>
> **Content first. Controls second. Technology invisible.**
>
> **Same AQENO. Same visual language. Different interaction models.**
>
> **Artwork is navigation, not decoration.**
>
> **Motion explains change. It does not demand attention.**
>
> **Complexity may exist in the system without appearing in the moment.**

AQENO should feel obvious before it feels powerful. The reference is iPod-like product simplicity,
not an imitation of an iPod's visual design.

`TARGET_GROUP_UX_CONCEPTS.md` explores four distinct interaction models within these boundaries. It
is UX discovery rather than an implementation contract: this blueprint must not be read as requiring
one layout whose only variation is text size, labels or element count.

## Existing contracts already covering this direction

The direction is mostly clarification, not a product change:

- `PRODUCT_FOUNDATION.md` already makes AQENO content-first, physical-first, adaptive, local-first,
  visually quiet and free of engagement or upsell mechanics.
- `DEVICE_UI_PRINCIPLES.md` already requires shallow navigation, one contextual primary action,
  progressive disclosure, large targets, calm failures and separation from administration.
- `DISPLAY_BEHAVIOR.md` and `DISPLAY_STATE_MACHINE.md` already define `INTERACTIVE → DIM → OFF`,
  make `AMBIENT` explicit and give Night/Dark-Room policy authority over all visible output.
- ADR 0012 already separates the in-process QML Device UI from a future authenticated Management UI.
- ADRs 0016 and 0017 already keep display policy in the application and make the display optional.
- `HARDWARE_REFERENCE.md` already fixes RH1's physical interaction mapping without making it a Core
  requirement.

## What the preview gets right

- a dedicated audio appliance rather than a desktop, dashboard or tablet shell;
- dark, high-contrast media presentation with calm surfaces and generous space;
- large, recognisable artwork as the primary content affordance;
- clear hierarchy in Now Playing: artwork, title, context, progress;
- few large touch targets and no dependence on precise gestures;
- physical controls visibly belonging to the product rather than looking added later;
- one coherent visual language across different information densities;
- semantic, restrained use of illuminated controls;
- visual polish through proportion, typography and motion rather than feature density.

## What AQENO does not take from the preview

| Preview element | AQENO decision |
|---|---|
| horizontal mode/app launcher | Do not adopt. AQENO has content and contextual views, not apps. |
| permanent touch Previous / Play-Pause / Next | Do not show by default on RH1. The physical controls already solve these actions. A later capability may expose touch transport for a concrete accessibility need. |
| clock/weather while “display off” | Contradicts authoritative `OFF`. `OFF` contains no pixels, clock or status. A clock would be explicit `AMBIENT`, never the fallback. |
| lit Bedtime Now Playing screen | Contradicts Night authority. Kids Bedtime skips `DIM` and reaches true `OFF`. |
| ordinary settings in primary navigation | Do not adopt. Immediate setup/recovery may use `SETUP`; administration belongs to the Management UI. |
| “Elternbereich” in the Device UI | Do not derive a Parent domain. Core roles remain User / Manager / Owner, and management stays a separate boundary. |
| usage-time dashboard | Do not introduce surveillance or engagement measurement from a mockup. |
| favourites, personal messages and Send to AQENO as current tiles | Future concepts only. They receive no surface until the domain capability and current use case exist. |
| Wi-Fi, Bluetooth, source or service status in normal media views | Technology remains invisible unless a concrete immediate recovery action requires it. |
| page dots, carousels and multiple Now Playing variants | Do not add as visual furniture. Use only after a real navigation or test need selects them. |

No unavailable capability appears disabled, locked, premium, purchasable or teased.

## Navigation model

The current Kids Early graph is deliberately tiny:

```text
explicit wake, idle ──> Home ──SELECT press──> Browse ──SELECT press──> Now Playing
                         ^                       |                          |
                         └────────── HOME ───────┴──────── HOME ────────────┘

explicit wake during playback ──────────────────────────────────────> Now Playing
```

Three surfaces and no more. HOME returns from any of them in one press, which is
what lets the graph stay a graph instead of a stack (ADR 0026 § 4).

> **THE DISPLAY SHOWS. THE HARDWARE OPERATES.**

- Startup renders nothing until `UI_READY`; it does not play a branded intro.
- A wake during playback opens Now Playing. A wake while idle opens Home.
- **Home is not an app grid.** One content area is dominant at a time; its neighbours are visible
  only as a hint that rotation has somewhere to go. Areas come from the content kinds ADR 0009
  already defines — Hörspiele, Hörbücher, Musik, Podcasts, Radio, Persönliches — and an area exists
  only while the library actually holds accessible items of that kind (P15). It is not a launcher
  for source- or protocol-specific applications, and never a grid of small icons.
- **Browse is one shallow level**: one dominant cover, its title, and a `3 / 18` position. A library,
  never a file manager. Neighbours are hinted at reduced size and opacity.
- Selecting artwork starts immediately and opens Now Playing. There is no confirmation.
- Now Playing has one clear, large Home action. Returning Home does not stop playback.
- Physical Previous, Play/Pause, Next and Volume do not navigate and do not wake the display. That
  rule is unchanged and is what keeps the dark room dark. Since ADR 0026 PREVIOUS and NEXT are
  content order in every context, so they never move focus on any surface, including a menu.
- **Navigation itself is physical** (ADR 0024, ADR 0026). SELECT moves focus, its press activates the
  focused item, and **HOME returns to Home from anywhere, at any time, without stopping playback**.
  Touch does the same things and is never required for any of them.
- There is no Back stack, drawer, tab bar, modal flow or hidden swipe in Kids Early. Whether a
  separate BACK control is ever needed is an open question that only a deeper browsing level can
  answer (ADR 0026 § 4); nothing is added in anticipation.

When a real library requires more than the bounded Home surface, one shallow content-browsing level
may be added over existing content/collection concepts. Its entry is content language (“Stories”),
not provider language, and it has one obvious return path. This blueprint does not implement or
define that collection model.

## Focus model

Encoder-first means the surface has a focus, not merely tappable areas.

- Exactly one element is focused on a surface that offers a choice. Home focuses a tile; Now Playing
  currently offers no choice and therefore no focus ring.
- Focus is visible from normal viewing distance: a heavy ring or clear elevation change plus a
  non-colour cue. A 1 px outline or a colour shift alone does not qualify.
- Rotation moves focus one item per detent and **wraps** at both ends. An endless knob must not run
  into an invisible wall, and a wrap is easier to explain to a child than a limit.
- Focus is a presentation state. It starts nothing, changes no audio and is not persisted.
- Touch selection does not move focus onto the tapped item and then require a second press. A tap
  activates directly, exactly as before.
- **The navigation input that wakes the display is consumed** and activates nothing, for the same
  reason a waking touch is consumed: nobody may trigger something they cannot see. Volume and
  Play/Pause are deliberately exempt — they are the blind-operable functions, and a swallowed first
  volume step in a dark room would break the very requirement the rule protects. **HOME is the other
  exception**: it wakes and acts in one press, because its outcome is the same in every context and
  a person in the dark should reach the way out once (ADR 0026 § 4).
- No everyday interaction uses a long press or a double press (ADR 0024 § A2).

## Actual UI surfaces

### Current

1. **Home** — one dominant content area with its name and item count; neighbours hinted.
2. **Browse** — one dominant item with title and position inside the area.
3. **Now Playing** — artwork, title, optional chapter/context, restrained progress and times.
   **No virtual transport row and no on-screen Home control**: all five of those actions are
   physical, and drawing them would invite reaching for the panel on a device whose display may be
   off. Paused is shown by the progress bar going quiet plus one small mark.
4. **Volume overlay** — transient, triggered by a volume change while the panel is already lit, and
   returning on its own. It never causes a wake.
5. **Notice overlay** — one calm sentence where an action produced no inherent feedback. The only
   case today is an unassigned token, and it appears only while the panel is already lit, because an
   unassigned token must never wake a dark display (`DISPLAY_STATE_MACHINE.md` note 7).

Empty library and playback failure are state treatments within those surfaces, not destinations or
modal screens. They remain calm, contain no technical language and never wake an `OFF` display.

### Future only when supported by a current use case

- **Favourites** — a direct content subset or assignment, not playlist administration; requires a
  domain decision before UI.
- **SETUP** — bounded pairing/recovery and simple immediate choices, not routine settings.
- **AMBIENT** — explicitly authorised passive content, never idle fallback.
- **Management UI** — separate authenticated surface for content, network, profiles and policy.

Personal messages, Send to AQENO and remote content are recorded future concepts. They do not add a
Device UI state today and must not become a notification centre later.

## Display-state presentation

| State | Device UI presentation | Interaction |
|---|---|---|
| `INTERACTIVE` | Complete current surface with its one contextual action | touch plus physical controls |
| `DIM` | small artwork plus title and at most one useful context line; no navigation or controls | touch only wakes and is consumed |
| `OFF` | no intended visible output; no clock, logo, progress or status | explicit wake accepted; physical playback remains active |
| `AMBIENT` | approved passive source under explicit authority | outside current slice |
| `SETUP` | bounded appliance setup/recovery | Manager/Owner authority; outside normal media navigation |

Night/Bedtime forces `OFF`, suppresses user-facing LEDs and never becomes a styled dark Now Playing
screen. Playback, volume and transport remain physically operable.

## Reference layout: 800 × 480

RH1 is designed at its real viewport first, not scaled down from a desktop composition.

This layout is RH1's, not AQENO's. The preferred later panel is roughly 4–5 inches (ADR 0025 § 1),
so information density must stay defensible on a substantially smaller surface: fewer simultaneous
items, larger focus treatment, no reliance on a 7-inch reading distance.

### Shared constraints

- fullscreen application surface; no title bar, taskbar, pointer or operating-system chrome;
- primary touch target at least **72 × 72 px**, with **84 × 84 px** preferred for isolated actions;
- essential information remains inside a 24 px edge-safe area;
- no more than three primary choices visible at once in Kids Early;
- text is supplementary for Kids Early: missing labels must not make artwork selection impossible;
- artwork is cropped consistently without stretching and remains recognisable at the rendered size;
- layouts must be inspected at exactly 800 × 480 and on the physical panel, not only at 1024 × 600
  or 1920 × 1080.

### Home

- one calm row of up to three large artwork tiles for the current slice;
- no app bar, provider badges, settings shortcut or permanent category rail;
- whitespace may remain unused;
- active content feedback is small and redundant in shape/icon as well as colour.

### Now Playing

- artwork occupies roughly 40–50% of the usable width;
- the remaining region holds title, optional context and restrained progress;
- one 84 px Home action sits in a stable edge position;
- RH1 touch transport controls are absent by default;
- long text truncates calmly rather than shrinking the entire hierarchy or causing scrolling.

### DIM

- materially fewer elements than Now Playing: smaller artwork, title and optional chapter only;
- no visible Home action, progress control, touch navigation or animation;
- normal Kids playback reaches `OFF` after the short configured hold; Night skips `DIM`.

## Physical controls and light

The control set is SELECT · PREVIOUS · NEXT · VOLUME · HOME (ADR 0026 § 2). RH1 can carry four of
the five with hardware on hand: three Cherry MX switches on the NeoKey and one encoder as VOLUME.

| Control | Action | Screen relationship |
|---|---|---|
| SELECT rotation *(hardware pending)* | move focus | wakes from `OFF`/`DIM`/`AMBIENT`; the waking input is consumed |
| SELECT press *(hardware pending)* | activate the focused item | wakes; the waking input is consumed |
| PREVIOUS MX key | previous item in content order (ADR 0009 § 2) | never wakes the display |
| NEXT MX key | next item in content order | never wakes the display |
| VOLUME rotation | relative volume | never wakes; a first step is never swallowed to light the screen |
| VOLUME press | Play/Pause | never wakes; the UI reflects it only when already visible |
| HOME MX key | return to Home; never stops playback | wakes, and **acts on the same press** |

Waking is a property of the control (ADR 0026 § 5): only SELECT and HOME can light the panel.
PREVIOUS and NEXT no longer change role by context, so nothing has to be resolved before the display
service can classify it.

RH1 has no SELECT control yet. Its bindings exist in the mapping registry, report as unavailable and
can be bound to any control a future adapter reports. Until then the complete touch-free journey is
exercised through the desktop simulator (`DEVELOPMENT.md`) rather than claimed for the assembled box
— but the physical path from Now Playing back to Home is no longer part of that gap: HOME closes it
on hardware already present.

These are safe device-wide defaults, not properties of the boards. The controlled mapping contract
in `PLATFORM_CONTRACTS.md` may assign another available AQENO action; hardware drivers still emit
only logical control events, and mappings remain independent of profiles, network and display state.

Lighting is semantic output, not decoration:

- default normal state is off or barely present only when a real observation shows value;
- a recognised intention may receive one short, calm acknowledgement;
- loading animation exists only for a wait the person must understand;
- error feedback is sparse, never alarming and never active under Night policy;
- `OFF` and Bedtime default all user-facing light to true off;
- colour never carries meaning alone, and no continuous rainbow, chase or pulse is permitted.

RH1 now has a semantic warm-light adapter with `off`, `subtle` and `clear` preferences. It deliberately
offers no raw RGB control, and Night/OFF override the preference to zero. Until physical true-off is
verified, failure to initialize the LEDs degrades explicitly to `NullStatusLeds` and remains an RH1
acceptance item rather than a software claim.

## Visual language

- dark, low-glare background; raised surfaces separated by tone rather than heavy borders;
- one calm primary accent, with secondary colours used only for distinct semantic meaning;
- soft but disciplined radii; consistent spacing and alignment;
- large content imagery without gradients, badges or overlaid technical metadata;
- modern, highly legible sans-serif typography with a dependable system fallback;
- interface icons are simple outline SVG assets; PNG is reserved for raster artwork and photos;
- missing artwork uses an AQENO-authored vector fallback, never a file/folder/Linux icon;
- focus, selection, playing, paused and failure states use shape/icon plus contrast, not colour alone.

Implementation should centralise visual tokens in one QML source. That is configuration for a
coherent product surface, not a runtime theme engine. Inter is a suitable OFL-1.1 font candidate and
Lucide a suitable ISC-licensed SVG candidate; selecting and bundling either remains an implementation
dependency decision with retained licence notices.

## Motion

- short press feedback, restrained crossfade and position-preserving surface transitions are useful;
- motion explains selection, navigation or a changed state;
- no permanent movement, bounce, decorative parallax, autoplaying carousel or animated idle state;
- reduced-motion capability removes non-essential transitions without changing layout or meaning;
- leaving `OFF` shows one complete frame; entering it has no farewell animation or flash.

## Adaptive interaction and accessibility

All configurations retain AQENO's identity, domain model, display-state contract and physical-control
semantics. They may nevertheless use different navigation structures, information hierarchies,
choice patterns and divisions of work between touch and hardware. Accessible / reduced complexity is
a voluntarily selected interaction model, not an age inference or a larger-font version of Standard.

The concept sheets in `TARGET_GROUP_UX_CONCEPTS.md` must be explored before shared implementation
abstractions are chosen. Current code remains scoped to Kids Early; the concepts neither authorise
four QML forks nor a generic profile renderer.

Every eventual composition still provides large targets, scalable text, visible focus, high
contrast, no mandatory precision gesture, no time-limited response and no meaning conveyed solely
through colour. Physical controls remain available for frequent playback when touch is difficult or
the display is off.

## Review gate for every main surface

Before accepting a surface, verify:

1. Can a person understand the available action without instructions?
2. Can a child identify relevant content from imagery?
3. Is the primary action unambiguous for a person needing reduced complexity?
4. Can it be operated without precision, speed or a hidden gesture?
5. Is any visible information useless in this moment?
6. Does a physical control already solve an on-screen action better?
7. Does the surface expose a source, service, hardware detail or unavailable capability?
8. Does it still work at exactly 800 × 480 with system chrome absent?

If an element can be removed without reducing understanding, remove it.

## Domain boundary

This blueprint needs no domain rewrite. Existing `ContentItem`, playback state, profile, role,
display policy and semantic input boundaries already support Home and Now Playing.

It explicitly does **not** create:

- apps, modes or provider-specific navigation;
- a generic theme/persona framework;
- favourites, messages, notifications or remote-send domain objects;
- Parent/Child roles or an on-device administration domain;
- collections or categories merely to match the concept preview;
- new display states for Home, Now Playing, Bedtime or failure.

Those concepts require their own present use case and domain review before they earn a UI surface.
