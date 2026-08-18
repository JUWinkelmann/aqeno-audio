# ADR 0024 — Physical-first interaction: touch is a capability, not a requirement

**Status:** Accepted
**Date:** 2026-08-18
**Amends:** `docs/product/DEVICE_UI_BLUEPRINT.md` § Navigation model and § Physical controls and
light; `docs/implementation/PLATFORM_CONTRACTS.md` § Physical controls; `DISPLAY_STATE_MACHINE.md`

## Context

AQENO's documents have said "physical first" since `PRODUCT_FOUNDATION.md` P06, but the implemented
Kids Early slice cannot be operated without touching the panel. Physical controls carry volume,
play/pause, previous and next; **selecting content and returning Home exist only as `TapHandler`s in
`ui/qml/Main.qml`.** `DEVICE_UI_BLUEPRINT.md` states this deliberately: "Physical Previous,
Play/Pause, Next and Volume do not navigate."

That was a defensible reading of physical-first while RH1's panel was assumed to be present and
touched. It is not compatible with the intended product: a future AQENO may have a display without
touch, and a person must be able to use AQENO in a dark room, with wet hands, from across a table,
or with motor limitations that make a 7-inch panel a poor primary control.

The target physical control set is also now known well enough to protect the abstraction against it,
while remaining far from a component decision.

## Decision

### 1. The interaction contract

> **Physical-first, display-assisted, touch-optional.**

The display serves orientation, artwork, status, selection, feedback and — later — time, timer and
alarm presentation. Everyday operation must never *require* it to be touched.

- No function is reachable only by touch.
- No navigation path requires touch.
- No touch-only gestures, swipe-only navigation, touch-only transport or hidden touch affordances.
- Existing touch affordances are kept. Touch remains a legitimate, comfortable input.

**This overturns the blueprint rule that physical controls never navigate.** Navigation now has its
own physical vocabulary (§ 2); transport controls keep their existing meaning and continue not to
navigate.

### 2. Semantic control vocabulary

Two distinct control roles exist above the hardware, and they never trade places:

| Role | Rotation | Short press | Long press |
|---|---|---|---|
| **NAV** — navigation | move focus | activate the focused item | reserved; back is under evaluation |
| **VOL** — volume/playback | volume down / up | play / pause | unassigned |

> **Volume stays volume. Play/Pause stays Play/Pause.**

A VOL control must never become contextual navigation, because eyes-free operation depends on a
control meaning the same thing in every state. Back-navigation is deliberately *not* fixed to a
dedicated button in this ADR; long press is a candidate and must be decided by real use with
children, adults and seniors, not by preference.

Transport (previous/next in the current playback context) belongs to a third control: on target
hardware a **momentary, centre-off two-way rocker**, not two separate front buttons. Whether its
directions mean previous item, previous chapter or seek is a contextual definition that remains open
(`USE_OBSERVATIONS.md` evidence required); no surprising multi-assignment is introduced meanwhile.

### 3. Navigation may wake; transport still may not

Physical navigation is the touch replacement, so it inherits touch's display semantics exactly, as a
new **Group G** in `DISPLAY_STATE_MACHINE.md`:

- from `OFF`, `DIM` or `AMBIENT`, a navigation input enters `INTERACTIVE` and **is consumed** — the
  navigation that wakes never also selects, exactly as note 2 requires for a waking touch. Rotating a
  knob in a dark room must not start something the person cannot see.
- in `INTERACTIVE` and `SETUP` it resets the visual timer and is delivered normally.

Volume, play/pause, previous, next and NFC keep their invariant: they never wake the display and
never reset the visual timer (invariant 3, note 6). The dark-room requirement is unchanged: the
device remains fully operable for listening while completely dark, and navigation is the one input
class whose entire purpose is looking at something.

### 4. RH1 controls are prototype input

The assembled Cherry MX/Qwiic controls stay in use and define nothing about the future product
layout. They are replaced later by NAV, VOL and the rocker without domain or application change,
because the boundary is and remains:

```text
physical input → logical control event → semantic AQENO action → application behaviour
```

RH1's three logical controls (`primary_left`, `primary_encoder`, `primary_right`) cannot express a
separate NAV encoder. The port therefore gains `navigation_encoder` as a logical control and the
mapping registry gains navigation actions; on RH1 no hardware reports that control, so the bindings
exist and are simply unavailable — the same honest state the contract already defines for missing
hardware. **RH1 cannot physically demonstrate touch-free operation with three controls**; the desktop
simulator can and does (§ 6).

### 5. Capabilities are reported, not framed

No capability framework, DSL, registry or plugin mechanism is introduced. ADR 0017 § 1 and ADR 0010
already rejected one, and the needed capability information already exists in the right places:

- input: `PhysicalInputSource.controls` reports each present control, its type, its events and
  whether it is illuminated;
- display: `DisplayPanel.capabilities()` reports authoritative off, brightness control and touch;
- audio, storage and network: their existing ports.

`touch = true` describes a possibility and never a product philosophy. Nothing in Domain or
Application may branch on a board name, and no code treats touch availability as permission to make
touch the primary path.

### 6. Touch-free acceptance

Operating AQENO without touch is a tested property, not an intention. The automated form covers the
current slice — wake, focus, select, play, pause, volume, previous/next, return Home — without a
single touch event. The physical form is an RH1 commissioning item
(`docs/hardware/RH1_VALIDATION_CHECKLIST.md`) and is complete only when the controls it needs exist.
Administration is explicitly outside this test; it belongs to the web client (ADR 0012, ADR 0018).

## Alternatives considered

**Overload the existing encoder with navigation when a menu is open.** Rejected: it breaks the
eyes-free guarantee that a control means one thing, and it is the specific failure § 2 exists to
prevent.

**Wait for the target hardware before adding navigation semantics.** Rejected: the UI would be
designed touch-first and retrofitted, which is exactly the sequence the product decision forbids.
The vocabulary is cheap; a touch-shaped information architecture is not.

**Remove touch from RH1.** Rejected: the panel is capacitive, touch works, and removing a working
input serves nobody. Not requiring it is the actual goal.

**Introduce a capability model as configuration.** Rejected under ADR 0017 § 1 and the project's
scope rule. Ports already report what hardware exists.

**Let navigation obey the transport rule and never wake.** Rejected: navigation without a visible
surface is meaningless, and a device that cannot be woken without touching it fails § 1.

## Consequences

- The Device UI has an explicit focus model. Every surface must show where focus is, what rotation
  will do and what a press will do — legible from normal viewing distance.
- The 800 × 480 RH1 layout is a prototype layout. Encoder-first information architecture must not
  assume that panel size (ADR 0025 § 1).
- ADR 0022's ownership confirmation observes `primary_left`, `primary_encoder` and `primary_right`
  short presses before action mapping. On target hardware those identities must be carried by the
  rocker directions and the VOL encoder, or the sequence must be redefined in that hardware's own
  decision. It must never migrate onto NAV alone.
- Mapping configuration can now express navigation, so a Manager can bind navigation actions to any
  reported control — including RH1's currently unused reserve keys, once an adapter reports them.
- Back-navigation semantics, rocker context semantics and the number of rules a person must learn
  remain open UX questions that only real testing can close.
