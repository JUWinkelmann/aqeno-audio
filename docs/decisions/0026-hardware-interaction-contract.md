# ADR 0026 — AQENO Hardware Interaction Contract

**Status:** Accepted
**Date:** 2026-08-19
**Supersedes:** ADR 0024 § A1 (four controls), § A3 (context-resolved LEFT/RIGHT), § A4 (per-action
wake classification of LEFT/RIGHT)
**Amends:** `PRODUCT_FOUNDATION.md` § 3 (new principles P21–P24) and § 5; `PLATFORM_CONTRACTS.md`
§ Physical controls and § LED contract; `DISPLAY_STATE_MACHINE.md` Group G;
`DEVICE_UI_BLUEPRINT.md`; `DEVICE_UI_PRINCIPLES.md`; `HARDWARE_REFERENCE.md`
**Normative companion:** `docs/implementation/INTERACTION_MATRIX.md`

## Context

AQENO's physical interaction has been decided in pieces. ADR 0024 established physical-first
operation and fixed four controls — NAV, VOL, LEFT, RIGHT — with LEFT and RIGHT resolved by content
context, and deliberately left one cell open (§ A3): what LEFT does on Now Playing during playback.
ADR 0025 made time a pillar without implementing it. Accessibility existed as principle P17
("accessibility through simplicity") but carried no physical rules, so nothing in the repository
said what makes a control findable in the dark or distinguishable by hand.

Three things forced this consolidation:

1. **Context-resolved controls fail the eyes-free test they were introduced to satisfy.** ADR 0024
   § 2 argued that eyes-free operation depends on a control meaning the same thing in every state —
   then made LEFT and RIGHT the exception. A person who cannot see the screen cannot know which
   context they are in, so they cannot know what LEFT will do. The open § A3 cell was not an
   oversight; it was the symptom.
2. **There was no reliable way out.** With back folded into LEFT's contextual resolution, the return
   path existed on the panel or nowhere. A child, an older person or anyone operating in the dark
   had no single control that always leads somewhere known.
3. **Hardware was being derived from available maker modules** rather than from interaction. The
   Qwiic encoder, the NeoKey and the Cherry MX switches on hand shaped the control vocabulary
   instead of the other way round. Every further purchase would have compounded that.

This ADR fixes the interaction first, so the next component decision follows from a contract instead
of from a parts drawer.

## Decision

### 1. Interaction posture

> **tactile first · illumination assisted · display enhanced · touch optional**

Seven principles bind every AQENO device and every hardware variant. Four of them are new durable
product rules and are recorded as `PRODUCT_FOUNDATION.md` P21–P24.

1. **Blind operation.** Every essential everyday action is performable without looking.
2. **Tactile identity.** Controls with different semantic roles are distinguishable by hand —
   through position, geometry or texture — without light and without labels.
3. **Invariant layout.** The spatial relationship of the essential controls is preserved across
   AQENO hardware variants. Muscle memory transfers between devices.
4. **Universal design.** Accessibility comes from good ordinary industrial design, never from a
   stigmatising special edition. **Accessibility without looking accessible.**
5. **Physical-first.** Physical controls guarantee access to every essential function.
6. **Touch-optional.** Touch may accelerate an interaction; it may never be required for one.
7. **Illumination-assisted.** Light supports operation and never defines it. Every control must be
   findable and operable with all illumination off.

There is one AQENO interaction model. There is no separate Kids, Adult, Senior or Accessible
operating logic. Mechanical adaptation — larger or grippier caps — is permitted and changes neither
electronics nor interaction logic.

### 2. The five controls

| Control | Rotation | Short press | Permanent role |
|---|---|---|---|
| **SELECT** rotary encoder | move focus / change a value | activate, confirm | navigation and value entry |
| **PREVIOUS** momentary button | — | previous item in content order | content order, never UI focus |
| **NEXT** momentary button | — | next item in content order | content order, never UI focus |
| **VOLUME** rotary encoder | volume down / up | play / pause | the two most frequent audio actions |
| **HOME** momentary button | — | return to the familiar AQENO starting point | the always-available way out |

Five tactilely findable positions, whose spatial relationship is invariant:

```text
    SELECT      PREV   NEXT      VOLUME
      ( )         <      >         ( )

                  HOME
```

**This schema fixes relationships, not enclosure coordinates.** Where the controls physically sit is
an industrial-design decision constrained only by § 6.

Each control has exactly one meaning in every state. No control changes role by context, no everyday
action uses a long press, a double press or a chord (ADR 0024 § A2 remains in force and now has no
exception at all).

### 3. PREVIOUS and NEXT are content order

They are not UI navigation and never move focus. Their meaning is the ordering of the current
content, defined per kind by ADR 0009 § 2 and unchanged by it:

| Context | PREVIOUS / NEXT |
|---|---|
| Music | previous / next track |
| Audio drama, audiobook | previous / next chapter, else −30 s / +60 s |
| Podcast | previous / next chapter, else −30 s / +60 s |
| Radio | previous / next favourite where favourites exist, otherwise ignored |
| Picture frame (`AMBIENT`) | previous / next image |
| A menu or browsing surface | **nothing** — they never move focus |

This closes ADR 0024 § A3: LEFT is no longer "back", so there is no undecided cell. The physical path
from Now Playing to Home is HOME, in every context, at all times.

Radio favourites are the one entry above that has no domain model yet; it is recorded as direction,
not as a promise, and needs the collection/favourite decision before it can be implemented.

### 4. HOME

HOME is a core control, not a configurable everyday key. Its semantics:

- **HOME always leads to the familiar AQENO starting point.** From any surface, at any time.
- **HOME never stops playback.** Returning home is a visual action, not a transport action.
- **HOME wakes a dark panel and is then executed, not consumed.** This is a deliberate exception to
  `DISPLAY_STATE_MACHINE.md` note 15. Consumption exists so nobody triggers a *context-dependent*
  action they cannot see; HOME's outcome is context-independent, non-destructive and identical every
  time. For a person operating in the dark, "press HOME, be home" must be one action, not two.
- **HOME resolves an interruptive state** — an expired timer, a ringing alarm, a failure treatment —
  by dismissing it. § 9 records the alarm hypothesis this rests on.
- HOME is not bindable to another action, and no other action is bindable onto HOME.

**Open, and not assumed:** whether AQENO also needs a separate BACK control. The current hypothesis
is that it does not, because the device information architecture stays deliberately shallow — but
that must be proved against real browsing depth, not asserted. Until a browsing level deeper than
one exists, the question cannot be answered honestly, and no BACK control is introduced in
anticipation.

### 5. Wake behaviour follows the control, again

ADR 0024 § A4 had to make wake behaviour a property of the resolved action, because LEFT and RIGHT
changed roles. With permanent roles that indirection is unnecessary and is withdrawn:

| Control | Display behaviour |
|---|---|
| SELECT rotate / press | wakes from `OFF`/`DIM`/`AMBIENT`; the waking input is consumed |
| HOME | wakes; **executed, not consumed** (§ 4) |
| PREVIOUS, NEXT | never wake, never reset the visual timer |
| VOLUME rotate / press | never wake, never reset the visual timer |

The dark-room guarantee is unchanged and now simpler to state: only SELECT and HOME can light the
panel, and only they are navigation.

### 6. Placement and mechanical behaviour

`PRODUCT_FOUNDATION.md` § 5 previously required that controls sit on the top or an angled upper
surface, so that pressing does not push the device backwards. That rule is replaced by the
requirement it was trying to express:

> **An ordinary one-handed press must not appreciably move AQENO on a normal surface.**

How that is achieved — rubber feet, mass, centre of gravity, enclosure geometry, actuation force —
is a mechanical decision. Controls may therefore also sit on a well-reachable inclined front face.

### 7. AQENO Rotary Control Contract

Rotary controls are specified abstractly. Adafruit, SparkFun and any other maker module is one
implementation of this contract, never its definition.

Required properties: incremental encoder; integrated push function; defined and clearly felt
detents; consistent direction (clockwise = forward/louder); a rotational torque and push force
usable by a child and by a person with reduced hand strength; a standardised shaft so caps are
exchangeable.

Preferences, not yet dimensional standards: a **6 mm shaft**, because the widest range of standard
caps fits it; SELECT and VOLUME as the **same** electrical and mechanical part, so the difference
lives entirely in the cap — fewer spare variants, one carrier footprint, simpler repair.

Cap size classes under evaluation: compact ≈ 24–26 mm, standard ≈ 30–32 mm, easy-grip ≈ 36–40 mm.
SELECT and VOLUME must be tactilely distinguishable — rim structure, concave/flat/convex top,
different knurling — without either looking like an assistive device.

Which encoder carries SELECT and which carries VOLUME is software configuration, not wiring destiny.

### 8. Device power states

AQENO distinguishes three device states. Only the first two occur in everyday use:

| State | Meaning |
|---|---|
| `ACTIVE` | in use |
| `SLEEP` | display dark, device fully operational and instantly usable |
| `OFF` | deliberately shut down |

> **You do not switch AQENO on and off. You use it.**

There is **no everyday power button on the primary control surface.** Any ordinary interaction may
bring AQENO out of `SLEEP`. A genuine shutdown control may exist away from the primary surface — the
rear or underside — or in local administration.

Two things this explicitly does not do: it does not accept cutting Raspberry Pi power as a product
definition of `OFF`, and it does not implement anything. Clean shutdown and power management remain
an open platform question. AQENO today has `ACTIVE` and `SLEEP` only, expressed as display state.

### 9. Night, darkness and control illumination

**`DARK` and `NIGHT` are separated**, because the existing contracts used one word for two things.

> **DARK means zero visible light.**

In the absolute dark state: display 0, control LEDs 0, status LEDs 0, no glowing HOME key, no
permanently visible clock, no unavoidable operating indicator. **No hardware may force visible
residual light.** This is a purchasing constraint, not only a software one.

Control illumination is **contextual guidance, never permanent status display**. It is never a
precondition for operation (§ 1.7). The night illumination policy has three named values, recorded
here so that nothing later invents a different vocabulary:

| Value | Behaviour |
|---|---|
| `off` | absolute dark; no illumination on approach or on any event |
| `on_approach` | dark until a hand approaches or an interruptive event occurs, then the relevant controls fade up gently and return to full off after a short inactivity period |
| `subtle` | deliberately dim continuous illumination, chosen by the user |

**Only `off` exists.** It is AQENO's current behaviour, it is the default, and there is no setting
to change it. `on_approach` is the expected long-term default and is deliberately not adopted now:
it requires proximity hardware no AQENO has validated, and shipping it as a preference would promise
behaviour AQENO cannot deliver. The names are provisional and belong to UX.

Consequently `DISPLAY_STATE_MACHINE.md` invariant 8 and note 12 hold today exactly as written: Night
forces every user-facing LED to true off. What this ADR changes is that the rule is no longer
*unconditional by definition* — it is the behaviour of the `off` policy, and a future policy chosen
deliberately by a person may offer brief, dim orientation instead. Absolute dark remains reachable,
remains the default and remains authoritative wherever a Bedtime scene requires it.

No RGB effects, no music visualisation, no blinking status.

### 10. Ambient light and proximity

AQENO may sense **ambient light** and **near-hand proximity**. Purpose:

- ambient light → adaptive display brightness and adaptive control illumination;
- proximity → recognise that a hand is approaching the control area, primarily so that a dark room
  can offer temporary orientation.

**Proximity is presence awareness and illumination assistance only.** It is never gesture control:
no waving for play/pause, no directional gestures, no hidden commands. Sensor failure must not
prevent normal operation — the controls remain fully usable and the illumination policy falls back
to its static behaviour.

**Sensor decision.** `VCNL4040` (ambient light + IR proximity, I²C) is the current target candidate
and would functionally replace the `VEML7700` (ambient light only), which RH1 already has. A later
AQENO reference device most likely needs one sensor, not both.

That "most likely" is not evidence. RH1 keeps its VEML7700 as the reference against which a
VCNL4040's ambient-light quality is measured — particularly at very low room brightness, where the
display-dimming and illumination decisions actually matter. **No claim that VCNL4040 suffices may be
made before that comparison exists**, and neither sensor is a mandatory production component. A
product may use the bare sensor, or a different compatible solution, on its own carrier.

Installation behind front material must be validated physically. IR transmission, internal
reflection, crosstalk and real detection range are not to be assumed from a datasheet.

**No `Proximity` port, adapter or illumination policy is implemented by this ADR.** No hardware
reports proximity, and inventing a policy for an unmeasured sensor is exactly what § 12 forbids.

### 11. NFC and the object area

NFC remains what ADR 0013 and `PRODUCT_FOUNDATION.md` § 7 already decided: an open shortcut layer,
never an access requirement. No content is reachable only through an AQENO token.

New, and physical:

> **Place, do not aim.**

The device must offer a **generous, flat object area**. Explicitly decided:

- **No recess and no well.** Standing objects and figures must work, simple 3D-printed objects must
  need no AQENO-specific under-geometry, and flat cards must work equally.
- The area is flat, generous, error-tolerant, suitable for standing objects, and findable by touch
  where that is possible without intrusive geometry — a slight material or texture difference, or a
  constructional seam, may be evaluated.
- The antenna solution is **not** decided here, and the enclosure must reserve adequate area from
  the start rather than discovering it later.

**Magnetic positioning** may be added later as an option: NFC identifies, magnetism may position and
hold. It must never become a precondition for NFC, ordinary cards and tags must keep working, no
proprietary magnet geometry becomes mandatory, and the interaction with the NFC antenna, speakers,
display and remaining electronics must be measured rather than assumed. No magnet arrangement is
specified.

### 12. Capabilities are documented, not framed

The optional hardware capabilities AQENO recognises are `DISPLAY`, `TOUCH`, `NFC`,
`AMBIENT_LIGHT`, `PROXIMITY`, `CONTROL_ILLUMINATION` and `BATTERY`.

**This list is a documentation artefact — the capability matrix in `HARDWARE_REFERENCE.md` — not a
runtime registry, DSL, plugin mechanism or configuration framework.** ADR 0010, ADR 0017 § 1 and
ADR 0024 § 5 rejected such a framework three times; nothing here reopens that. Where code needs to
know whether hardware exists, the existing ports already report it: `PhysicalInputSource.controls`,
`DisplayPanel.capabilities()`, the audio, storage and network ports, and the composition root's
adapter selection. A capability with no hardware has no UI surface (P15) and no branch in Domain or
Application.

The five controls of § 2 are **not** in that list. They are the AQENO interaction contract itself: a
device that cannot express them is a prototype stage, not a variant.

### 13. Prototype hardware is not product hardware

RH1 may use a Raspberry Pi 4, the 7-inch touch panel, the HiFiBerry MiniAmp, Qwiic/STEMMA breakouts,
Cherry MX switches, the VEML7700 and later a VCNL4040 breakout. **None of that defines production
hardware.** A later device may use its own carrier board, directly mounted encoders, integrated
sensors, a different SBC, a different display and a different bus architecture, as long as it
satisfies this contract.

The order of work is fixed and is the point of this ADR:

```text
product interaction → hardware interaction contract → mechanical/electrical requirements
   → RH1 test → component decision
```

Never the reverse. No component is purchased on the strength of this document.

## Alternatives considered

**Keep four controls and context-resolved LEFT/RIGHT (ADR 0024 § A1/A3).** Rejected: it is the
source of the problem. A control whose meaning depends on invisible context cannot be operated
without looking, which is the guarantee the same ADR asks for.

**Solve the return path with a long press or a double press on an existing control.** Rejected under
ADR 0024 § A2 and P17. Timed gestures fail exactly the people AQENO is meant to serve: children,
older people, tremor, varying press durations, poor learnability.

**Leave the return path on touch.** Rejected: it makes the panel mandatory for one essential
everyday action, which contradicts ADR 0024 § 1 and cannot work on a device without touch.

**Give HOME a second function (favourites, menu, profile).** Rejected: a safe return point that
sometimes does something else is not a safe return point.

**Consume the HOME press that wakes, like every other navigation input.** Rejected in § 4: it costs
a blind user a doubled action for the one control whose outcome is never surprising.

**Introduce a runtime capability framework for the seven capabilities.** Rejected for the fourth
time — see § 12.

**Buy a VCNL4040 now and drop the VEML7700.** Rejected: the ambient-light comparison is the whole
reason RH1 keeps the sensor it has, and the bus/mounting contract is not settled.

**Decide the NFC antenna and a magnet arrangement now.** Rejected: both are measurements. Reserving
the area and forbidding a recess is what actually constrains the enclosure.

## Consequences

- **The touch-free journey gains its missing return path.** HOME closes the one gap ADR 0024 § A3
  left open, on the box rather than in the simulator.
- **RH1 can carry four of the five controls with hardware already on hand.** HOME becomes a Cherry
  MX switch on a free NeoKey position; PREVIOUS and NEXT move to adjacent positions so the transport
  pair reads as a pair and HOME is physically separated (Tactile Identity). Only SELECT still needs
  hardware that does not exist. See `HARDWARE_REFERENCE.md` § RH1 control plan.
- **Logical controls are renamed to their permanent roles** — `previous`, `next`, `volume_encoder`,
  `select_encoder`, `home` — because positional names (`primary_left`) described a control whose role
  was context-dependent, and that is no longer true. Control bindings persisted under the old names
  are not recognised and fall back to the defaults, which is the documented behaviour for a missing
  binding entry. No production device holds custom bindings today.
- The semantic navigation event `Back` becomes `Home`, and the action `navigation.back` becomes
  `navigation.home`. There is no back event, because there is no back control.
- ADR 0022's ownership-confirmation sequence keeps working and reads better: PREVIOUS → VOLUME press
  → NEXT observes three permanent control identities instead of three positional ones, which removes
  the migration caveat ADR 0024 recorded for target hardware.
- `DISPLAY_STATE_MACHINE.md` Group G loses its context-resolution clause and gains a HOME exception.
  Invariant 8 becomes conditional on the night illumination preference, whose default preserves it.
- The interaction is now provable rather than asserted: `INTERACTION_MATRIX.md` is normative for what
  each control does in each situation, and the questions it cannot answer are listed there rather
  than guessed.
- Time capabilities inherit a control vocabulary before they are built (ADR 0025 § 3 amendment): the
  visual timer is set with SELECT and left with HOME. The ringing-alarm hypothesis in
  `INTERACTION_MATRIX.md` § 5 is the one place where a control's permanent meaning is under real
  tension, and it is recorded as open rather than decided.
- Purchasing is now gated on this contract. The current "do not buy" list is in `SHOPPING_LIST.md`.
