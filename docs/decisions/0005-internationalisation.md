# ADR 0005 — Internationalisation: German and English

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

AQENO must support **German and English** from the start, with translation quality treated as a
product property rather than a late chore. Two things make this less trivial than "add a language
file":

- **`P03 Local first`.** Runtime machine translation via a cloud API is excluded outright: it would
  break offline operation, add a network dependency to the UI, and send interface and possibly
  content strings to a third party. There is no acceptable version of this.
- **Kids Early requires no reading at all** (`USER_JOURNEY_KIDS_EARLY.md`). So the child-facing
  surface is nearly textless by design, and almost all translatable text lives in the
  Manager/Owner surfaces — setup, library management, NFC assignment, scenes, policies.

That asymmetry is useful: the strings that need the most care are read by adults, and the surface
read by a three-year-old should stay free of text rather than be translated well.

A further distinction the domain must respect: **UI language and content language are independent.**
A German audiobook in an English UI is normal and its title must never be translated or
transliterated.

UI stack is Qt/QML per ADR 0002; licensing constraints per ADR 0004.

## Decision

### 1. Mechanism

**Qt's own translation system**: `tr()` in Python, `qsTr()` in QML, `.ts` source files, compiled to
`.qm` and shipped with the application. No additional i18n dependency.

`lupdate` and `lrelease` are build-time Qt tools. They are used, not distributed, so their licence
does not affect AQENO's — the same relationship as a compiler to its output. Noted explicitly
because ADR 0004 is strict and this would otherwise look like a violation.

### 2. Source language and authored German

- **Source language for UI strings is English**, matching the codebase and documentation convention
  in `ONBOARDING.md` § 6.
- **German is authored, not translated.** For any string a user actually reads, the German wording is
  written by a native speaker to sound natural, then reconciled with the English — not produced by
  running the English through a translator. "Einwandfrei" is not reachable by translating
  developer-written English literally.
- **No string ships in a language it has not been reviewed in.** A missing translation falls back to
  English; a wrong or machine-sounding translation is worse than a fallback.

### 3. German conventions, decided once

Inconsistency here is what makes translations feel amateurish, so these are fixed now:

- **Address form: `Du`**, throughout, including the Manager surfaces. AQENO is a family device, not
  business software. Applied consistently — mixing `Du` and `Sie` is the most visible defect in
  German software.
- **No anglicisms where a natural German word exists** — but no forced translations of established
  terms either. `Podcast` stays `Podcast`; `Scene` becomes `Szene`; `Manager` as a *role name* is
  resolved in the glossary (gap G22), because role names appear in both code and UI and must not
  drift apart.
- **Compound nouns over noun phrases** where German would naturally compound.
- Numbers, dates, times, durations and decimal separators come from the locale, never from
  hand-formatted strings.

### 4. Rules that keep translation possible

- **No string concatenation to build sentences.** Word order differs; concatenation makes correct
  German impossible. Use full sentences with placeholders.
- **Plurals go through Qt's plural handling**, never through `if count == 1`.
- **Every string carries a disambiguation comment** where its meaning is not obvious from the text.
  Isolated words like "Off", "Play" or "Next" are ambiguous without context and are exactly where
  translators guess wrong.
- **No text baked into images or icons.**
- **Layouts must tolerate German length.** German UI strings commonly run 30–50 % longer than
  English; large touch targets must not break when a label grows. This is a QML layout requirement,
  and it is verified with a pseudo-localisation pass rather than by eye.
- **Umlaut-correct sorting.** Library sorting uses locale-aware collation, so `Ärger` sorts near
  `Arger`, not after `Z`. A naive byte sort produces a visibly broken library list in German.

### 5. Language selection

- The UI language is an **explicit AQENO setting**, not inferred from the system locale — AQENO is an
  appliance and its own setting must be authoritative.
- Initial value is offered during `SETUP`, defaulting to the system locale when it is German or
  English.
- **Language is a device/profile setting, not a per-session choice a child can trigger.** It is
  Manager-controlled for child profiles, consistent with the role model.
- Changing language must not require a restart and must not interrupt playback.

### 6. Explicitly out of scope

Right-to-left layout, additional languages, translated content metadata, text-to-speech and voice
input. The mechanism must not make later languages hard, but no work is done for them now.

## Alternatives considered

**GNU gettext (`.po` files) via Python's `gettext`.** The more familiar format, larger tooling
ecosystem, and translators generally prefer it. Rejected because the UI is QML: Qt's system is
already integrated with `qsTr()` and QML's engine, and mixing two i18n mechanisms in one application
splits the string catalogue in half for no benefit.

**Runtime machine translation via a cloud API.** Rejected outright — see Context. Incompatible with
local-first operation, and it would send interface strings and potentially content titles to a third
party, which also makes it a data-protection question rather than only a technical one.

**Ship German only initially, add English later.** Simpler short term, and the first users are
German. Rejected because retrofitting i18n means touching every string in the UI, and because
English as the source language is what keeps the codebase consistent with its own documentation
convention.

**Separate German and English builds.** Rejected: two artefacts to test and package, for a device
that may be used by a bilingual family.

## Consequences

**Easier.** Because Kids Early is textless by design, the translation surface is small and
concentrated in adult-facing screens. The `Du` decision and the no-concatenation rule remove the two
most common sources of bad German before any string is written.

**Harder.** Every user-visible string now needs native German review before release, which is a
real recurring cost and a genuine release gate. QML layouts must be built for text expansion from
the start rather than tightened around English. The pseudo-localisation pass is additional test
work.

**Constrained.** No dynamic sentence assembly anywhere in the UI. Locale-aware collation must be in
place before the library list is built, not bolted on after — retrofitting it means changing the
sort key of persisted data.

**Interaction with the domain model.** `ContentItem` needs a content-language field distinct from
the UI language, so the library can display and sort mixed-language content correctly without ever
translating a title. This is an addition to `DOMAIN_MODEL.md` and should be made when gap G14
(content ingestion) is closed.
