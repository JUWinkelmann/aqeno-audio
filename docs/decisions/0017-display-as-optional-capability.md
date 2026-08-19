# ADR 0017 — Display as an optional capability

**Status:** Accepted
**Date:** 2026-08-18
**Accepted:** 2026-08-18

## Context

AQENO is an audio-first appliance. ADR 0016 established that display policy belongs to the
application and that a panel adapter applies resolved power and brightness. The first implementation
used a fake panel unconditionally, however, so the composition root still assumed that some display
implementation existed.

At the same time, the existing `DIM` state had no concrete Kids Early use. Real playback benefits
from a brief, glanceable Now Playing presentation before the screen disappears, but idle AQENO must
not turn into a clock or smart display. The accepted `AMBIENT` state already means an explicitly
enabled and authorised passive mode such as a photo frame; reusing that name for automatic playback
information would reverse its product invariant.

## Decision

### 1. A display is optional

> **Display is a capability, not a dependency.**

The composition root selects either a concrete panel adapter or a null panel. The null panel reports
`authoritative_off=True`, `brightness_control=False` and `touch=False`; applying power or brightness
to it is a harmless no-op. Core playback, physical input, NFC launch, persistence and readiness do
not depend on a panel being present.

Display detection remains composition-root work. There is no capability DSL, plugin mechanism or
runtime hotplug. A panel choice is made once at process construction.

### 2. `DIM` is the glanceable playback presentation

The existing states keep their meanings:

- `INTERACTIVE` — complete active UI;
- `DIM` — glanceable, deliberately reduced presentation;
- `OFF` — no intended visible output;
- `AMBIENT` — explicitly enabled and authorised passive mode;
- `SETUP` — bounded appliance setup.

Glanceable is a presentation of `DIM`, not a sixth state. During active playback, an experience
profile that allows it follows `INTERACTIVE → DIM → OFF`. `DIM` contains no visible touch controls,
navigation or attention-seeking animation. The first Kids Early prototype tests reduced Now Playing
variants without selecting a final visual design.

When playback is idle, inactivity goes to `OFF`. Night/Bedtime also goes directly to `OFF`; it never
enters or remains in glanceable `DIM`. `AMBIENT` remains reachable only through an explicit request
or an authorised schedule and retains the invariant: **Ambient is never an automatic fallback for
inactivity.**

### 3. Ambient light is an input, not domain state

An `AmbientLight` port reports illuminance in lux. A VEML7700 adapter owns the sensor register and
conversion details. Display/device policy may smooth readings and apply a small hysteresis before
mapping them to panel output; raw lux and sensor mechanics do not enter the domain display machine.

This is not a generic adaptive-brightness engine. The policy exists only to prevent visible
brightness oscillation on Reference hardware and remains bounded by the active profile's configured
brightness. Night/Bedtime and `OFF` retain authority regardless of a sensor reading.

*Amended 2026-08-19 by ADR 0026 § 10:* near-hand **proximity** is a candidate second input of the
same class — a sensor reading that informs illumination policy, never domain state and never a
gesture. It has no port, adapter or policy, because no AQENO hardware reports it. The sensor
comparison it depends on (VCNL4040 against the existing VEML7700) is an RH1 measurement, and § 1's
refusal of a capability framework covers it unchanged.

For the first feasibility implementation, only `DIM` reacts: readings use an exponential smoothing
factor of 0.25, enter the dark band at 10 lux, leave it at 15 lux, and cap output there at half the
configured `DIM` brightness (minimum 1). These are fixed experiment mechanics, not Manager settings;
they must be revisited with the sensor mounted in the RH1 enclosure. Sampling cadence belongs to the
future concrete RH1 composition and is not invented before the hardware exists.

## Alternatives considered

**Rename or repurpose `AMBIENT`.** Rejected because it would invalidate P14 and the accepted state
machine. Automatic playback information and an authorised photo frame have different authority and
attention semantics.

**Add a sixth `GLANCEABLE` state.** Rejected because the existing `DIM` state already represents the
required transition, timer and power behaviour. The distinction is presentational.

**Require a fake or real panel in every process.** Rejected because it makes a presentation device a
construction-time dependency of an audio player and hides the headless case from tests.

**Runtime display discovery and hotplug.** Rejected for the current slice. It adds lifecycle and
failure semantics without a current use case.

**A reusable adaptive-brightness framework.** Rejected. One sensor, one calm policy and the Reference
prototype are the current need.

## Consequences

AQENO can start and remain a complete token/physical-control audio device with no display attached.
Choosing content that has no assigned token remains unavailable headlessly; unavailable UI is absent
rather than rendered as locked.

Kids Early gains a short, playback-only glanceable phase. Its duration, brightness and visual content
are Reference-prototype parameters to validate in real use. Night remains reliably dark, and idle
behaviour remains `OFF`.

The Device UI must render `DIM` differently from `INTERACTIVE`; lowering the brightness of the same
screen is not sufficient. The exact reduced Now Playing variant remains a UX experiment.
