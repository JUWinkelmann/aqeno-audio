# AQENO Admin — UX Redesign Report

**Status:** Design direction + representative screens (v2)
**Date:** 2026-08-18
**Supersedes visually:** `admin/src` prototype UI (functional reference only)

---

## Current UI problems

### Information architecture
- Navigation mirrors backend entities (Tokens, Profile, Gerät, Einstellungen) instead of user jobs.
- **Quellen** hidden on mobile; **Mehr** links only to Profile, not a proper overflow.
- No **Prüfen** (review) surface — uncertainty is invisible until user opens each item.
- **Hinzufügen** has four inconsistent entry points (toolbar, FAB, drag-drop, empty state) with different capabilities.

### UX patterns that feel like admin tooling
- Profile detail = number input + Speichern (sysadmin CRUD).
- Settings = raw schema fields (Entprellung ms, symbolische Links).
- Audience editing duplicated: per-item form + bulk modal with different interaction models.
- Title edit: click-without-affordance; no inline save feedback.
- Token grid shows raw UID; NFC labeled technically.

### Copy & language
- **„API GAP“** shown to end users in Profiles, Sources, Add sheet.
- English mixed in: „Upload“, „Profile“, operation `type` enums on Start.
- Technical diagnostics exposed (database, nfc adapter states).

### Import experience
- Upload queue shows file progress only — no analysis narrative.
- No grouping review; user never sees „3 Hörspiele erkannt“.
- Operation `result` has only aggregate counters — UI cannot show created works.

### Artwork
- Thumbnail URL === full artwork URL (performance + no size strategy).
- Cover is small in grid; not interactive; no drag-drop on cover.
- No bulk „fehlende Cover ergänzen“ — API does not exist.
- Placeholder = first letter in grey box (feels broken, not designed).

### Mobile
- Three stacked bottom layers: tab bar + selection bar + upload queue.
- Media detail = fullscreen overlay, not sheet navigation.
- FAB bypasses Add sheet (no sources link on mobile add path).

### Accessibility
- Modals lack focus trap, `role="dialog"`, Escape handling.
- Selection only via explicit mode — no long-press.

---

## New information architecture

Built from **user jobs**, not API tables.

| Job | Nav label | What it answers |
|---|---|---|
| Orient | **Start** | Was ist los? Was soll ich als Nächstes tun? |
| Browse & organise | **Mediathek** | Was habe ich? |
| Resolve uncertainty | **Prüfen** | Was sollte ich kurz bestätigen? (badge when count > 0) |
| People & access | **Personen** | Wer hört was? |
| Physical play | **Tags** | Welche Karte startet was? |
| Device | **AQENO** | Wie geht es dem Gerät? Einstellungen? |

**Not in primary nav:**
- **Hinzufügen** — persistent primary action (FAB desktop corner / mobile center-adjacent). Opens import flow.
- **Speicherorte** — under Mediathek segment + AQENO → Speicher.
- **Einstellungen** — inside AQENO, not top-level clutter.

### Why this is better
- „Prüfen“ makes automation visible — user sees AQENO did work, only uncertainty remains.
- „Personen“ not „Profile“ — listening contexts, not accounts.
- „Tags“ not „Tokens“ — matches physical product language.
- „AQENO“ consolidates device health + settings — one mental model for „the box“.

---

## Design principles

1. **Automate certainty. Ask about uncertainty.** — Routine metadata never forms; review queue for exceptions.
2. **Artwork is content.** — Covers are large, interactive, first-class.
3. **Progressive disclosure.** — Common path is 1–2 taps; technical detail in „Details“.
4. **Calm by default.** — No KPI dashboard; contextual cards only.
5. **Explicit choice wins.** — Manual artwork/metadata never silently overwritten.
6. **No AI theater.** — „12 Kapitel erkannt“, not „✨ Magic“.
7. **Honest about limits.** — Missing API = internal gap docs, not user-facing errors.

---

## Design language

### Character
Ruhig · hochwertig · warm · präzise · eigenständig — not SaaS, not NAS admin.

### Color (light; dark prepared)
| Token | Light | Role |
|---|---|---|
| `canvas` | `#F5F3EF` | App background — warm linen |
| `surface` | `#FFFFFF` | Cards |
| `surface-muted` | `#EBE8E2` | Placeholders, chips |
| `ink` | `#1C1916` | Primary text |
| `ink-muted` | `#6B6560` | Secondary |
| `accent` | `#B85C38` | Primary action — deep terracotta |
| `accent-soft` | `#F3E8E3` | Selected states |
| `success` | `#3A6B52` | Positive |
| `attention` | `#9A7B2F` | Review / prüfen |

### Typography (system stack)
| Role | Size | Weight |
|---|---|---|
| Display | 1.75rem | 600 |
| Title | 1.125rem | 600 |
| Body | 0.9375rem | 400 |
| Caption | 0.8125rem | 500 |
| Label | 0.75rem | 500, +0.02em |

### Spacing & shape
- Base unit 4px; comfortable rhythm 16/24/32.
- Card radius 16px; artwork radius 12px; pills full-round.
- Touch targets minimum 48px on mobile.

### Artwork placeholder
Generated from title + kind — soft gradient, large initial, kind icon — never grey file icon.

### Motion
120ms feedback · 200ms panels · respect `prefers-reduced-motion`.

---

## Key journeys — steps before / after

| Journey | Before | After (target) |
|---|---|---|
| A: 3 MP3s from phone | Connect → Library → FAB → file picker → queue bars → hunt in library | Hinzufügen → pick → „3 Dateien werden gelesen“ → „1 Hörspiel erkannt“ → done (or 1 Prüfen item) |
| B: 40 chapter audiobook drag | Drop → 40 progress bars → 40 grid items? | Drop → grouped progress „Pettersson Folge 12 · 14 Kapitel“ → 1 card in library |
| C: Fix missing cover | Find item → detail → no cover UI → ? | Prüfen → „Cover fehlt“ → tap cover → Foto/Suchen/Drop → saved |
| D: 18 missing covers | Impossible at scale | Prüfen → „18 ohne Cover“ → [Sichere ergänzen] — **blocked: API GAP bulk artwork** |
| E: Wrong cover | Detail → no artwork edit | Cover tap → Ersetzen → upload/search |
| F: 20 media for 2 profiles | Select mode → Freigeben modal | Select → Personen-Chips → sofort angewendet |
| G: Tag assign | Tokens → wizard auto-starts NFC | Tags → „Tag halten“ calm wait → pick cover visually |
| H: NAS add | API GAP message | Speicherort → guided — **blocked: API GAP mount** |
| I: NAS offline | Warning card | Calm inline on Speicherort + Start |
| J: 5 review items | Does not exist | Prüfen tab with 5 cards |

---

## Artwork pipeline

### Backend today (domain)
1. Manual PUT `/artwork` → stored in artwork dir, wins permanently.
2. Embedded tags (MP3/M4A/FLAC) on ingest.
3. Sidecar files `cover|folder|front` + jpg/png/webp on ingest.
4. Existing DB artwork path reused on re-scan.
5. **Not exposed:** provenance, external provider, series fallback.
6. **Not implemented:** generated placeholder server-side, derivatives.

### Client v2 behaviour
- Display `artwork_thumbnail_url` when present.
- **Placeholder** generated client-side (title + kind) — UI-only until API provides `generated`.
- Cover tap → sheet: Foto/Datei, Bild hier ablegen (desktop), Entfernen.
- PUT multipart on save — real API.
- **No fake search** — „Cover suchen“ shows „Demnächst“ + API GAP reference.

### Artwork API gaps
| Gap | Need |
|---|---|
| G-A1 | `artwork_source` on MediaDetail: manual \| embedded \| sidecar \| generated |
| G-A2 | True thumbnail endpoint or `?size=card` |
| G-A3 | `GET /library/review-queue?kinds=missing_artwork,uncertain_grouping` |
| G-A4 | `POST /library/artwork/bulk-resolve` |
| G-A5 | `GET /artwork/search?q=` backend metadata adapter |
| G-A6 | Undo for artwork/metadata batch |

---

## Import pipeline

### Backend today
- `POST /imports` → operation `media_import`.
- `result`: `{ candidates_seen, works_touched, works_marked_unavailable }`.
- Domain groups by folder, extracts metadata, artwork — not reported per work.

### Client v2 behaviour
- Grouped upload UI by inferred folder name.
- Analysis screen shows honest steps with available data:
  - ✓ Dateien hochgeladen (Uppy)
  - ✓ Bibliothek aktualisiert (operation completed)
  - ○ Details — **API GAP:** no per-work breakdown
- Poll/SSE `operation.changed`.

### Import API gaps
| Gap | Need |
|---|---|
| G-I1 | `created_media_ids[]` + titles in operation result |
| G-I2 | `import_stages[]` with labels for UI checklist |
| G-I3 | `grouping_suggestions[]` with confidence |
| G-I4 | Batch/tus upload |
| G-I5 | Review queue entries for uncertain imports |

---

## Representative screens implemented (v2)

| # | Screen | Route | Status |
|---|---|---|---|
| 1 | Start | `/` | Redesigned |
| 2 | Mediathek | `/library` | Redesigned |
| 3 | Media Detail | `/library?id=` | Redesigned + artwork edit |
| 4 | Import | Sheet `/import` + FAB | Redesigned |
| 5 | Prüfen | `/review` | UI + partial API (missing artwork via query) |
| 6 | Mobile | Same routes | Bottom nav + sheets |

---

## Responsive strategy

| Breakpoint | Pattern |
|---|---|
| <768px | Bottom nav (5 items), full-width sheets, cover actions via bottom sheet |
| 768–1023px | Narrow rail optional; library 2-col grid |
| ≥1024px | Sidebar + library grid + detail pane 400px |

---

## Performance (large libraries)

- Unchanged: cursor pagination, infinite scroll, debounced search, lazy images.
- New: artwork `loading="lazy"`, `decoding="async"`, aspect-ratio boxes prevent layout shift.
- Review queue: **requires API** for scale — v2 queries `artwork_thumbnail_url IS null` via listing pages with honest „Teilansicht“ until G-A3.

---

## Remaining migration

After v2 acceptance:
- Personen: bulk access flows (not per-item forms) — `AudienceEditor` still v1
- Tags: live capture UX polish (wizard still v1 component)
- AQENO settings: human-language pass on `SettingsForm` / `SourceList`
- Remove old `lib/components/shell/AppShell`, `MediaGrid`, `MediaCard`, primitives where superseded
- Dark mode pass
- Serve `admin/build` from device (deployment integration per API_CLIENT_GUIDE)

Completed in v2 slice:
- New shell (`Shell.svelte`), design tokens (`lib/ui/tokens.css`)
- Routes `/people`, `/tags`, `/aqeno` with redirects from `/profiles`, `/tokens`, `/device`, `/settings`
- Global import sheet via `importStore`
- E2E updated for password auth + new navigation

---

## API GAP summary (user-facing features blocked)

| Feature | Status |
|---|---|
| Cover search | Blocked — no endpoint |
| Bulk cover resolve | Blocked |
| Full review queue | Partial — missing artwork detectable per page only |
| NAS add | Blocked |
| Podcast/Radio add | Blocked |
| Import work breakdown | Blocked |
| Profile create | Blocked |
| Artwork thumbnails | Same URL as full image |
