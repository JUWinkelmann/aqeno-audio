# ADR 0023 — Product identity, pillars and the attention principle

**Status:** Accepted
**Date:** 2026-08-18
**Amends:** `PRODUCT_FOUNDATION.md` § 1 and § 2

## Context

AQENO has been described as an "open, adaptive, audio-first player platform". That description is
accurate about playback and says nothing about two capabilities the product has always implied and
partly recorded as unscheduled concepts: time (sleep timer, morning scene, bedtime) and personal
connection (`Send to AQENO`, F1). Without a canonical identity, each of those arrives as a feature
argument rather than as something the product already is, and every future request has to be judged
against a definition that does not mention it.

At the same time an audio device that gains a clock, a timer and message delivery is one careless
step away from a smart display. `PRODUCT_FOUNDATION.md` P12, P14 and P15 already forbid the
individual mechanics, but no single statement says what AQENO refuses to become.

## Decision

### 1. Identity

> **AQENO is a calm everyday companion for audio, time and personal connection.**

Audio remains the primary and defining pillar; time and personal connection are AQENO's other two
pillars, not appendages. Depending on user and configuration, one AQENO may be an audio, audiobook,
music or podcast player, an internet radio, a clock, an alarm clock, a modern radio alarm, a visual
timer, a routine helper, or the recipient of selected personal content.

### 2. Three pillars as the feature test

A capability qualifies for consideration only if it supports at least one pillar —
**AUDIO**, **TIME**, **PERSONAL CONNECTION** — and is compatible with a calm, non-distracting
device. This test is applied *before* the decision order in `AGENTS.md` § "Deciding what to build";
passing it grants consideration, never implementation.

### 3. What AQENO is not

AQENO is not a smartphone, tablet, smart display, Alexa/Google-Home-class smart speaker, game
platform, social device, news portal or general information dashboard. No development proceeds
toward a news feed, weather dashboard, browser, app store, games, social feed, advertising,
engagement mechanics or arbitrary notifications. This makes F17 in
`docs/product/FUTURE_PRODUCT_CONCEPTS.md` a product-level non-goal rather than a catalogue entry.

### 4. Attention principle

> **Smart, in AQENO, means the device takes work off a person — not that it creates as many
> interactions as possible.**

AQENO may present information and may draw attention to a relevant event. It may not compete for
attention: no engagement loops, artificial badges, unnecessary animation, permanently changing
content, recommendations whose purpose is usage time, "discover more" mechanics or unnecessary
notifications. When AQENO is not needed it must be able to recede visually and acoustically.

This is a product principle (`PRODUCT_FOUNDATION.md` P19), not a theme, mode or setting.

### 5. Send to AQENO stays bounded

`Send to AQENO` (F1) is the canonical expression of the personal-connection pillar: an audio
message, a reminder, selected content or a personal signal from an authorised person. It is not a
general notification system and must never carry advertising, social feeds, promotional messages or
third-party push. Trust relationships and recipient authorisation remain part of the capability, not
an afterthought. The cloud/comfort service that would deliver it remains separate from the local
Core (ADR 0010, ADR 0018) and is not decided here.

### 6. Nothing here schedules implementation

This ADR changes the definition of the product, not the current milestone. Clock, alarm, timer and
`Send to AQENO` remain future concepts and receive no Device UI surface, domain object or dependency
until their own product decision exists (see ADR 0025 § 3 for the time capabilities).

## Alternatives considered

**Keep the audio-only definition and treat time and messages as features.** Rejected: it makes every
such capability argue for its existence from outside the product definition, which is how a device
either stays accidentally narrow or grows by exception.

**Define AQENO broadly as a "calm smart device".** Rejected: without the explicit non-goals in § 3
that description permits exactly the dashboard AQENO must not become.

**Record the attention principle as a UI guideline.** Rejected: it constrains product scope, not
presentation, and a guideline is negotiable in a way this is not.

## Consequences

- The pillar test is a documented gate in `AGENTS.md`; a capability outside all three pillars is
  declined without further analysis.
- Time capabilities stop being anomalies in an audio product and become legitimate future work under
  ADR 0025 — with no implementation licence.
- `FUTURE_PRODUCT_CONCEPTS.md` remains the backlog; its F17 non-goal is now product-level.
- The identity does not weaken local-first (ADR 0010): every pillar must have a useful local form.
