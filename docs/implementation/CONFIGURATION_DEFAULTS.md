# Configuration Defaults

**Date:** 2026-08-17
**Closes:** gap G05

Every value here is a **default with a range**, not a constant. They are starting points chosen to be
adjusted at the device, and several are guesses that user testing will move. What matters for
implementation is that no value is invented at the call site.

Startup and wake performance targets are **not** repeated here. They live in
`PLATFORM_CONTRACTS.md` § Reference performance targets and must not be duplicated.

Columns marked **Fixed** cannot be changed at runtime. **Manager** values are editable by Manager or
Owner. Nothing in this document is editable from a child-facing surface.

---

## 1. Display timeouts

Seconds of no *visual* interaction before the transition fires. Physical transport events do not reset
these timers — see `DISPLAY_STATE_MACHINE.md` note 6.

| Profile | Inactivity → `DIM`/`OFF` | Range | `profile_allows_dim` | Editable |
|---|---:|---|:---:|---|
| Kids Early | **30** | 10–120 | no | Manager |
| Kids Reader | **45** | 10–180 | no | Manager |
| Kids Explorer | **60** | 10–300 | no | Manager |
| Easy | **90** | 15–600 | no | Manager |
| Standard | **120** | 15–900 | yes | Manager |

| Timer | Default | Range | Editable |
|---|---:|---|---|
| Night override for all profiles | **10 s** | 5–30 | Manager |
| `DIM` hold before `OFF` (Standard only) | **15 s** | 5–60 | Manager |
| `SETUP` idle → `OFF` | **300 s** | 60–900 | Manager |
| `SETUP` idle → `OFF` while `night_active` | **60 s** | 30–300 | Manager |

Kids profiles never use `DIM`: `DISPLAY_BEHAVIOR.md` § Kids default requires the transition to go
straight to `OFF`. `DIM` exists in the state machine so it is not invented later, and is reachable
only for Standard.

## 2. Brightness

Logical 0–100. The display adapter maps these to hardware; `OFF` is not a brightness value but an
absence of output.

| Setting | Kids Early | Other Kids | Easy | Standard | Editable |
|---|---:|---:|---:|---:|---|
| `INTERACTIVE` | **70** | 80 | 85 | 85 | Manager |
| `DIM` | n/a | n/a | n/a | **10** | Manager |
| `AMBIENT` | **40** | 40 | 50 | 50 | Manager |
| Night minimum (any state) | **5** | 5 | 5 | 5 | Manager |

| User-facing LEDs | Default | Editable |
|---|---:|---|
| Normal interaction brightness | **20** | Manager |
| Night brightness | **0 — true off** | **Fixed** |

The night LED value is fixed at zero. `PRODUCT_FOUNDATION.md` § 6 makes it a core product requirement,
not a preference, and a configurable "dark room" that can be switched to "slightly lit" is not the
feature that was specified.

---

## 3. Volume — safety-critical

**Treat this section differently from the rest.** Hearing damage is the one plausible personal-injury
path that runs through AQENO's own code rather than a component manufacturer's, and the device is for
an actual three-year-old. ADR 0006 § 6 records why these are safety requirements with tests, not
comfort settings.

### 3.1 Scale

Volume is a **logical perceptual value 0–100**. The audio adapter maps it to gain with a documented
curve — default `gain = (v/100)³` — applied **inside the pipeline**, never by changing the system
mixer, so other software cannot move AQENO's ceilings (ADR 0003).

### 3.2 Ceilings

| Ceiling | Default | Range | Editable |
|---|---:|---|---|
| Child profile absolute maximum | **70** | 30–70 | Manager, **cannot exceed 70** |
| Night ceiling | **35** | 15–50 | Manager |
| Headphone path (where detectable) | **55** | 20–60 | Manager |
| Easy / Standard maximum | **100** | 50–100 | Manager |

**Rules, each of which is a test:**

- A ceiling is never raisable from a child-facing surface.
- The child maximum of 70 is a hard bound: a Manager may lower it, never raise it above 70.
- When a ceiling drops below current volume, volume is reduced immediately.
- The night ceiling applies the moment `night_active` becomes true, mid-playback included.
- Where headphone presence is detectable, the lower ceiling applies on connect, without user action.
- Ceilings are enforced in the application layer, not in the UI, and hold for every input path:
  encoder, touch, NFC Action and scene.

### 3.3 The honest caveat, and how to remove it

**Logical 70 is not a hearing-safety guarantee.** It is a percentage of an unknown amplifier and an
unknown speaker; the same value can be harmless or dangerous depending on hardware. The numbers above
are conservative placeholders that prevent the obvious failure — a child at 100 % — but they are not
calibrated.

For orientation, WHO–ITU guidance on safe listening (H.870) uses **75 dB(A)** as a reference exposure
level for sensitive users including children, against 80 dB(A) for adults. Treat that as the target to
calibrate toward, not as a compliance claim.

**Calibration procedure**, to be run once on Reference hardware and repeated whenever the amplifier or
speaker changes — this is a P2 feasibility task:

1. Place a sound-level meter at **0.5 m** from the speaker, at a child's likely head position.
2. Play pink noise, or a normalised sample of typical content, at logical volume 100.
3. Record dB(A) at 100, 90, 80, 70, 60, 50, 40, 30.
4. Set the child maximum to the highest logical value measuring **≤ 75 dB(A)**.
5. Set the night ceiling to the highest value measuring **≤ 60 dB(A)**.
6. Set the headphone ceiling by the same method, measured per an appropriate headphone method.
7. Record the measurements and the resulting values in this document, and replace the placeholders.

Until step 7 is done, the placeholders stand and this caveat stays in place.

### 3.4 Behaviour

| Setting | Default | Range | Editable |
|---|---:|---|---|
| Encoder step per detent | **3** | 1–10 | Manager |
| Volume at first boot | **40** | 0–ceiling | Manager |
| Fade on play start | **150 ms** | 0–500 | Fixed |
| Maximum instantaneous jump | **5** | — | **Fixed** |

Volume persists across restarts and is clamped to the applicable ceiling on load. No acceleration on
fast encoder rotation in the MVP: predictability matters more than speed, and an accelerating volume
control in a child's hands is the wrong trade.

---

## 4. Playback and resume

| Setting | Default | Range | Editable |
|---|---:|---|---|
| Resume position persist interval while playing | **10 s** | 5–60 | Fixed |
| Rewind applied on resume | **3 s** | 0–10 | Manager |
| Item counted as finished | **remaining < 30 s or ≥ 98 %** | — | Fixed |
| Acceptable resume error after power loss | **≤ 12 s** | — | Fixed |

Position is also persisted immediately on pause, stop, item change, profile change, scene change and
orderly shutdown.

The 3 s rewind is deliberate: re-entering an audiobook a few seconds earlier restores context. The
acceptable error follows from the 10 s interval — an unexpected power cut may lose up to one interval,
and that is the durability requirement persistence must meet (gap G09).

**Streams and live radio persist no position.** The port reports seekability, so the application
treats "no resume position" as a property of the content, not as a failure (ADR 0003).

## 5. Scenes and sleep timer

| Setting | Default | Range | Editable |
|---|---:|---|---|
| Sleep timer duration | **30 min** | 5–120 | Manager |
| Offered presets | **15 / 30 / 45 / 60 min** | — | Manager |
| Fade-out before sleep stop | **20 s** | 0–60 | Manager |
| Action at sleep-timer end | **pause** | pause / stop | Manager |

Pause rather than stop, so the resume position survives and the next morning continues where the night
ended.

## 6. NFC

| Setting | Default | Range | Editable |
|---|---:|---|---|
| Same-UID re-trigger debounce | **2000 ms** | 500–5000 | Manager |
| Acknowledgement tone for unassigned tag | **off** | on / off | Manager |
| Acknowledgement tone while `night_active` | **never** | — | **Fixed** |

An unassigned tag produces no display wake (`DISPLAY_STATE_MACHINE.md` note 7) and no error text. It
is logged and otherwise ignored — a three-year-old presenting the wrong object should experience
nothing happening, not a failure.

---

## 7. Where these live

One settings store, per the persistence contract, with three tiers:

1. **Fixed** — constants in code, not in the settings file. Changing them is a code change and an ADR
   where a contract is affected.
2. **Manager** — in the settings file, editable through an authorised management surface, validated
   against the ranges above on read *and* on write. An out-of-range persisted value is clamped and
   logged, not honoured. ADR 0012 does not require that surface to live on the box.
3. **Derived** — calibration results from § 3.3, stored with the measurement date so a stale
   calibration is visible.

Ranges are enforced in the application layer. A UI that cannot produce an out-of-range value is not
sufficient: the settings file is editable by hand and must be treated as untrusted input.
