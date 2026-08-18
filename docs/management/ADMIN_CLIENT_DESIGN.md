# AQENO Administration Client — Design Proposal

**Status:** Implemented (vertical slices 1–10)
**Date:** 2026-08-18
**API contract:** `docs/management/openapi.json` v1.0.0

This document delivers deliverables A–H from the Administration Client brief before major implementation begins.

---

## A — Information Architecture

### Design principle

Navigation follows **user jobs**, not API resource trees. The user thinks in media, tokens, profiles and device health — not in operations, collections as ACL objects, or ingestion jobs.

### Top-level areas (6 + contextual)

| Area | User question | Rationale |
|---|---|---|
| **Start** | What matters right now? What should I do next? | Contextual home, not a KPI dashboard. Surfaces only actionable, timely information. |
| **Mediathek** | Where is my content? | Primary daily surface. Search, browse, detail, bulk actions, visibility. |
| **Tokens** | Which card starts what? | Distinct physical workflow; deserves dedicated, visual space. |
| **Profile** | Who listens and what can they hear? | Profiles are warm identities, not accounts. Content access lives here *and* in Mediathek — not as a separate ACL area. |
| **Gerät** | How is AQENO doing? | Human summary first; diagnostics behind disclosure. |
| **Einstellungen** | How should AQENO behave? | Product settings only — never a junk drawer for features. |

**Not a permanent nav item:**

- **Hinzufügen** — always reachable as primary action (FAB on mobile/tablet, prominent button in Mediathek header on desktop, global drag-and-drop overlay). Adding content is too important to bury in a menu.
- **Quellen** — lives under Mediathek → „Quellen“ segment and Gerät → Speicher. Not a protocol-oriented top-level item.
- **Freigaben** — no separate menu. Visibility is edited in Mediathek (single + bulk) and Profile (profile-centric view). Collections appear as „Sammlungen“ inside Profile and bulk flows when API supports grouping UX.

### Mediathek internal model

Avoid raw `ContentKind` tabs. Use **human collections** backed by API filters:

| UI segment | API filter | Label (DE) |
|---|---|---|
| Alles | none | Alles |
| Geschichten | `kind=audio_drama` | Hörspiele |
| Bücher | `kind=audiobook` | Hörbücher |
| Musik | `kind=music_album,music_track` * | Musik |
| Podcasts | `kind=podcast_episode` | Podcasts |
| Radio | `kind=radio_stream` | Radio |
| Aufnahmen | `kind=personal_recording` | Aufnahmen |
| Nicht verfügbar | `available=false` | Momentan nicht erreichbar |

\* Music may require two queries or a future API `kind` group — see API Gaps.

Sort: title (default, matches server cursor order), recently added (needs API), duration.

### Start screen content (conditional cards)

Show only when relevant:

1. **Gerade läuft** — `GET /playback` when `state` is playing/paused.
2. **Import läuft** — active operations from `GET /operations` where `type` is import/scan and `state` is queued/running.
3. **Neue Inhalte** — recent items via library query (limited); hidden when library empty.
4. **Unzugeordnete Tokens** — tokens with `assigned_media_id: null` from `GET /tokens`.
5. **Quelle offline** — `GET /media-sources` where `available=false`.
6. **Nächster Schritt** — empty-state CTA when library or tokens are empty.

No fixed KPI tiles. No „7/7 services healthy“.

### Search scope

| Context | Scope |
|---|---|
| Mediathek toolbar | `GET /library/media?search=` (server-side, debounced 250 ms) |
| Tokens | Local filter on loaded token list (small cardinality expected) |
| Profile picker | Local filter on `GET /profiles` |
| Global (desktop ⌘K) | Mediathek search first; extend when API offers cross-entity search |

### Settings grouping

| Group | Source |
|---|---|
| Audio & Lautstärke | `SettingsResource.volume`, per-profile volume in `ProfileResource` |
| Display & Nacht | `SettingsResource.display`, `brightness`; profile display policies |
| Mediathek-Verhalten | `SettingsResource.library` (roots, scan on startup, symlinks) |
| NFC | `SettingsResource.nfc` |
| Wiedergabe | `SettingsResource.resume`, `sleep_timer` |
| Sprache | `SettingsResource.language` |
| Administration | password change, logout, about, diagnostics link |
| Erweitert | raw paths, technical IDs, restart-required notices |

All settings mutations show `apply_mode: restart_required` honestly.

---

## B — Responsive Navigation

### Breakpoints

| Name | Range | Primary pattern |
|---|---|---|
| `mobile` | 360–767 px | Bottom tab bar + full-screen routes + bottom sheets |
| `tablet` | 768–1023 px | Collapsible rail + split content/detail |
| `desktop` | ≥ 1024 px | Fixed sidebar + content + optional detail pane |

### Mobile (360 px+)

```
┌─────────────────────────┐
│  AQENO · Wohnzimmer  ⚙  │  ← compact header, connection dot
├─────────────────────────┤
│                         │
│      Route content      │
│                         │
│                    [+]  │  ← FAB: Hinzufügen (not in tab bar)
├─────────────────────────┤
│ Start │ Mediathek │ …   │  ← 4 tabs + „Mehr“
└─────────────────────────┘
```

**Tab bar:** Start · Mediathek · Tokens · Mehr
**Mehr sheet:** Profile · Gerät · Einstellungen · Quellen

- Media detail: full-screen push navigation with back gesture.
- Bulk select: enters selection mode via long-press or explicit „Auswählen“; bottom action bar appears.
- Upload queue: persistent bottom sheet (collapsed pill → expanded panel).
- Token assignment: full-screen wizard.

### Tablet (768 px+)

```
┌──┬────────────────┬──────────┐
│▐▌│   Mediathek    │  Detail  │  ← optional detail pane ≥ 900 px
│  │   grid/list    │  pane    │
│  │                │          │
└──┴────────────────┴──────────┘
```

- Icon rail (72 px) replaces bottom tabs; labels on hover/long-press.
- Library + detail split when width ≥ 900 px and item selected.
- Upload: side panel or bottom sheet depending on orientation.
- Profile + content access: split list | access editor.

### Desktop (1024 px+)

```
┌──────────┬─────────────────────┬─────────────┐
│ Sidebar  │   Mediathek         │   Detail    │
│ 240 px   │   toolbar + grid    │   pane      │
│          │   infinite scroll   │   360 px    │
└──────────┴─────────────────────┴─────────────┘
```

- Sidebar: Start, Mediathek, Tokens, Profile, Gerät, Einstellungen.
- **Hinzufügen** in sidebar footer + drag-anywhere overlay on Mediathek.
- Detail pane toggles; ⌘K global search; keyboard: ↑↓ navigate list, Enter open detail, Esc close.
- Shift+click range select in list/grid.

### Connect / first launch (all form factors)

Full-screen connect flow before shell:

1. Product: same-origin `/api/v1` below `http://aqeno.local`; Vite proxies the same path in development.
2. `GET /auth/status` selects first setup, password login or an existing session.
3. First setup/recovery: Previous → Encoder → Next at AQENO, then choose a local Admin password.
4. Login establishes an HttpOnly session cookie; the tab retains only its CSRF token.
5. `GET /device` confirms readiness, then the shell opens.

Direct URL editing is hidden under diagnostics. The technical Management key never appears in this
journey. Offline / unreachable: calm retry screen, no technical stack traces.

---

## C — Design Direction

### Product feel

Modern, warm, precise — adult-facing sibling of AQENO Device UI. More information-dense than Kids UI, but never „enterprise admin“. Restraint over decoration.

### Typography

| Token | Size | Weight | Use |
|---|---|---|---|
| `display` | 1.75 rem / 28 px | 600 | Page titles |
| `title` | 1.25 rem / 20 px | 600 | Section headers, media titles |
| `body` | 1 rem / 16 px | 400 | Default text |
| `caption` | 0.875 rem / 14 px | 400 | Metadata, secondary |
| `label` | 0.75 rem / 12 px | 500 | Uppercase-sparing labels |

Font stack: **system-ui** stack only (no external fonts — local/offline requirement).

```
font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
```

### Color (light mode first; dark follows)

| Token | Value | Use |
|---|---|---|
| `--surface-base` | `#FAF9F7` | App background — warm off-white |
| `--surface-raised` | `#FFFFFF` | Cards, panels |
| `--surface-sunken` | `#F0EEEA` | Input backgrounds |
| `--text-primary` | `#1A1814` | Primary text |
| `--text-secondary` | `#5C574F` | Secondary |
| `--accent` | `#C45E3A` | Primary actions — warm terracotta (AQENO family) |
| `--accent-hover` | `#A84E30` | Hover |
| `--success` | `#3D7A5A` | Positive states |
| `--warning` | `#B8860B` | Uncertain import grouping |
| `--danger` | `#B83A3A` | Destructive |
| `--border` | `#E5E1DA` | Dividers |
| `--focus-ring` | `#C45E3A66` | Keyboard focus |

Semantic states never rely on colour alone (icon + text).

### Spacing & radii

- Base unit: **4 px**. Common steps: 8, 12, 16, 24, 32, 48.
- Card radius: **12 px**. Buttons: **10 px**. Sheets: **16 px** top corners.
- Touch targets: **minimum 44 × 44 px** on mobile/tablet.

### Elevation

Subtle shadows only on floating elements (FAB, sheets, dropdowns):

```css
--shadow-float: 0 4px 24px rgba(26, 24, 20, 0.08);
```

### Motion

| Duration | Use |
|---|---|
| 120 ms | Micro-feedback (toggle, checkbox) |
| 200 ms | Panel open/close, route transitions |
| 300 ms | Upload progress, success confirmation |

`prefers-reduced-motion: reduce` → instant transitions.

### Artwork

- Lists: `artwork_thumbnail_url` with lazy loading + neutral placeholder (initials or kind icon).
- Detail: full `artwork_url`.
- Broken/missing: generated placeholder from title initials on `--surface-sunken`.

### Icons

Lucide Svelte, 20 px inline / 24 px navigation, 1.5 px stroke.

---

## D — Core User Journeys

### D1 — Connect

| Step | UI | API |
|---|---|---|
| Enter URL + key | Connect form | `GET /device` |
| Success | Show device name, enter app | — |
| Failure | „AQENO nicht erreichbar“ + retry | — |

### D2 — Library browse (10k+)

| Step | UI | API |
|---|---|---|
| Open Mediathek | Skeleton grid | `GET /library/media?limit=50` |
| Scroll | Infinite load | `?cursor=` opaque |
| Search | Debounced input | `?search=` |
| Filter segment | Chip row | `?kind=` / `?available=` |
| Profile lens | Profile chip | `?profile_name=` |
| Open item | Detail view | `GET /library/media/{id}` |

### D3 — Upload desktop (drag & drop)

| Step | UI | API |
|---|---|---|
| Drag over Mediathek | Overlay highlight | — |
| Drop files | Queue groups by folder/name heuristic | — |
| Per file upload | Uppy → multipart | `POST /imports` (one file each) |
| Track progress | Grouped queue UI | `GET /operations/{id}` or SSE |
| Complete | Toast + refresh list | `GET /library/media?search=` |
| Review | Open detail if needed | `GET /library/media/{id}` |

*Import result shows scan summary, not created work IDs — see API Gap I1.*

### D4 — Upload smartphone

| Step | UI | API |
|---|---|---|
| Tap FAB | Action sheet: Dateien / Kamera-Roll | — |
| Pick files | Native file picker, `multiple` | — |
| Upload | Collapsed group progress | `POST /imports` × N |
| Background | User navigates freely | poll/SSE operations |

### D5 — NAS / sources (read-only v1)

| Step | UI | API |
|---|---|---|
| View sources | Card per source with status | `GET /media-sources` |
| Offline NAS | „Momentan nicht erreichbar“ calm card | `available=false` |
| Add NAS | **Blocked** — document API Gap | — |
| Rescan | Button triggers scan | `POST /library/scans` |

### D6 — Podcast add

| Step | UI | API |
|---|---|---|
| Search | **Blocked** — API Gap | — |
| RSS fallback | **Blocked** — no subscribe endpoint | — |

*v1: show „Demnächst“ empty state; do not call external RSS from browser.*

### D7 — Radio add

| Step | UI | API |
|---|---|---|
| Search directory | **Blocked** — API Gap | — |
| Manual stream URL | **Blocked** — no create endpoint | — |

*v1: existing `radio_stream` items browsable if already in library.*

### D8 — Token assign

| Step | UI | API |
|---|---|---|
| Start | „Token zuordnen“ wizard | `POST /token-captures` |
| Wait | Animated pulse + „Halte Token an AQENO“ | poll or SSE `token.capture_changed` |
| Detected | Haptic/visual success | `GET /token-captures/{id}` → `detected` |
| Pick content | Searchable media picker | `GET /library/media?search=` |
| Confirm | Summary card | `PUT /token-captures/{id}/assignment` |
| Done | Token list with artwork | `GET /tokens` + media thumbnails |

### D9 — Profile access (single medium)

| Step | UI | API |
|---|---|---|
| Open medium detail | Section „Sichtbarkeit“ | — |
| Toggle | ● Alle / ○ Ausgewählte Profile | `POST /content-access/bulk` `set_shared` or `set_selected_profiles` |
| Per-profile | Checkbox list with avatars | same endpoint |
| Explain | „Warum?“ link | `GET /library/media/{id}/access/{profile}` |

### D10 — Bulk access

| Step | UI | API |
|---|---|---|
| Select items | Selection mode | — |
| Action bar | „Für Profile freigeben“ | — |
| Pick profiles | Sheet with profile chips | `POST /content-access/bulk` |
| Confirm | Count summary | returns `BulkAccessResult` |

### D11 — Media detail & edit

| Step | UI | API |
|---|---|---|
| Header | Artwork, title, kind, duration | `GET /library/media/{id}` |
| Primary actions | Token zuordnen (not play — no remote control in API) | — |
| Chapters | Read-only list | from detail |
| Edit metadata | Inline edit title/kind/language | `PATCH /library/media/{id}` |
| Artwork | Replace/remove | `PUT/DELETE .../artwork` |
| Remove | Confirm „Aus Mediathek entfernen“ | `DELETE /library/media/{id}` |

### D12 — Device status

| Step | UI | API |
|---|---|---|
| Summary | „AQENO läuft einwandfrei“ or specific issue | `GET /device` |
| Storage | Human bar (used/free) | `storage_*_bytes` |
| Now playing | Optional card | `GET /playback` |
| Details | Expand diagnostics | `GET /diagnostics` |

---

## E — API Mapping (journey → endpoints)

| Journey | Endpoints |
|---|---|
| Connect | `GET /device` |
| Library list/search/filter | `GET /library/media` |
| Library detail | `GET /library/media/{id}` |
| Edit metadata | `PATCH /library/media/{id}` |
| Artwork | `GET/PUT/DELETE /library/media/{id}/artwork` |
| Remove media | `DELETE /library/media/{id}` |
| Upload | `POST /imports` → `GET /operations/{id}` |
| Library scan | `POST /library/scans` → operations |
| Active jobs | `GET /operations`, SSE `operation.changed` |
| Sources view | `GET /media-sources`, `GET /settings` (library.roots) |
| Tokens list | `GET /tokens` |
| Token detail/unassign | `GET /tokens/{uid}`, `DELETE /tokens/{uid}/assignment` |
| Token assign flow | `POST /token-captures`, `GET /token-captures/{id}`, `PUT .../assignment`, SSE |
| Playback card | `GET /playback`, SSE `playback.changed` |
| Profiles | `GET /profiles`, `GET/PUT/DELETE /profiles/{name}` |
| Favorites | `GET /profiles/{name}/favorites`, `PUT/DELETE .../favorites/{media_id}` |
| Progress | `GET /profiles/{name}/progress/{media_id}` |
| Content access | `POST /content-access/bulk`, `GET /library/media/{id}/access/{profile}` |
| Collections | `GET/POST /collections`, `PUT/DELETE /collections/{id}`, `PUT .../audience` |
| Settings | `GET/PUT /settings` |
| Device | `GET /device`, `GET /diagnostics` |
| Live updates | `GET /events` (SSE) |

**Authentication:** Menschen melden sich mit dem lokalen Admin-Passwort an. Der Browser verwendet
danach ein HttpOnly-Session-Cookie und einen CSRF-Token für Mutationen. Der technische Management-Key
bleibt nur ein nicht in OpenAPI sichtbarer Diagnose-/Recovery-Weg; Listening Profiles sind keine
Authentifizierungsidentitäten.

**Artwork URLs:** returned as paths relative to API host; client prefixes configured base origin.

---

## F — API Gaps

Documented gaps — client must not invent workarounds.

### G1 — Device discovery & local ownership — **CLOSED**

| Field | Value |
|---|---|
| Use case | User opens admin app, finds „Wohnzimmer-AQENO“ without typing IP |
| Data needed | Friendly local URL, mDNS/Bonjour records, secure physical ownership confirmation |
| Implemented | Avahi publishes `http://aqeno.local`; first setup and recovery require the deliberate RH1 sequence Previous → Encoder → Next; the browser then sets a local Admin password |
| Client work | No key handover or manual URL entry in the normal product journey |

### G2 — Podcast directory & subscribe

| Field | Value |
|---|---|
| Use case | Search „Sendung mit der Maus“, subscribe, episodes appear in library |
| Data needed | Search results (title, artwork, feed URL); subscribe creates/updates show + episodes |
| Reason | No podcast endpoints in OpenAPI; only `podcast_episode` kind in library |
| Proposed extension | `GET /podcasts/search?q=`, `POST /podcasts/subscriptions {feed_url}` → Operation |

### G3 — Radio directory & add station

| Field | Value |
|---|---|
| Use case | Search „Deutschlandfunk“, add to library |
| Data needed | Search results (name, logo, stream URL); add creates `radio_stream` work |
| Reason | No radio endpoints; streams only appear via scan/ingestion |
| Proposed extension | `GET /radio/search?q=`, `POST /radio/stations {station_id}` or `{stream_url}` |

### G4 — NAS mount & connection test

| Field | Value |
|---|---|
| Use case | Add family NAS, test connection, see file count, add to library roots |
| Data needed | CRUD for mounted sources, connection test, file count estimate |
| Reason | `GET /media-sources` is read-only; roots only via `PUT /settings.library.roots` (absolute paths, restart) |
| Proposed extension | `POST /media-sources` with test probe; `POST /media-sources/{id}/test` |

### G5 — Profile creation

| Field | Value |
|---|---|
| Use case | Manager creates „Anna“ profile with Kids Early level |
| Data needed | `POST /profiles` with defaults |
| Reason | Only `GET /profiles` and `PUT /profiles/{name}` (update existing) |
| Proposed extension | `POST /profiles` returning `ProfileResource` with sensible defaults |

### G6 — Import result detail

| Field | Value |
|---|---|
| Use case | After upload, show „Wir haben ein Hörspiel erstellt: Pettersson …“ with link |
| Data needed | `created_media_ids[]`, optional `grouping_suggestions[]` with confidence |
| Reason | Operation `result` only has `candidates_seen`, `works_touched`, `works_marked_unavailable` |
| Proposed extension | Extend import operation result schema in OpenAPI |

### G7 — Batch / resumable upload

| Field | Value |
|---|---|
| Use case | 200 files, resume after network drop |
| Data needed | Multi-file endpoint or tus; per-batch operation |
| Reason | `POST /imports` accepts one `file` per request; no tus |
| Proposed extension | tus endpoint or `POST /imports/batch`; client keeps Uppy adapter swappable |

### G8 — Media list audience summary

| Field | Value |
|---|---|
| Use case | Grid shows lock icon / „Nur Anna & Paul“ without N+1 requests |
| Data needed | Optional `audience_summary` on `MediaSummary` |
| Reason | Audience only via per-media access endpoint or bulk context |
| Proposed extension | Optional field on list items or `GET /library/media/audience-summary?ids=` |

### G9 — Kind filter groups

| Field | Value |
|---|---|
| Use case | Single „Musik“ filter for albums + tracks |
| Data needed | `kind` query accepting multiple values or `kind_group=music` |
| Reason | `kind` is single `ContentKind` enum |
| Proposed extension | `kind` as array or grouped filter param |

### G10 — Recently added sort

| Field | Value |
|---|---|
| Use case | Start screen „Zuletzt hinzugefügt“ |
| Data needed | `sort=recent` or `last_seen` on `MediaSummary` |
| Reason | Cursor order is title + UUID only; `last_seen` only on detail |
| Proposed extension | `sort` query param; expose `last_seen` on summary |

### G11 — Remote playback control

| Field | Value |
|---|---|
| Use case | „Abspielen“ from admin to test content |
| Data needed | `POST /playback/play` etc. |
| Reason | `GET /playback` is read-only by design |
| Proposed extension | Out of scope for v1; UI omits play button or shows „Am Gerät abspielen“ |

### G12 — Network / Wi-Fi settings

| Field | Value |
|---|---|
| Use case | Configure Wi-Fi from admin |
| Reason | Explicitly CONTRACT ONLY in `LOCAL_MANAGEMENT_API.md` |
| Proposed extension | Future `PUT /network` when hardware port exists |

### G13 — Settings apply without restart

| Field | Value |
|---|---|
| Use case | Immediate volume/display change |
| Reason | All settings return `apply_mode: restart_required` |
| Client behaviour | Show honest „Änderung gespeichert — Neustart erforderlich“ banner |

---

## G — Performance Plan

### Targets

| Metric | Target |
|---|---|
| Initial JS (gzip) | < 150 KB route shell + lazy chunks |
| Time to interactive (dev LAN) | < 2 s on mid-range phone |
| Library scroll | 60 fps with 50-item pages |
| Search response feel | < 300 ms perceived (skeleton immediately) |
| 20k library browse | Same UX as 200 — no full client mirror |

### Data strategy

1. **Never** fetch full library. Page size 50, `useInfiniteQuery` with opaque cursors.
2. **Search/filter server-side** — debounce 250 ms, cancel in-flight requests.
3. **Detail on demand** — `MediaDetail` only when pane/route opens.
4. **Artwork** — lazy `loading="lazy"`, thumbnail URLs only in lists.
5. **SSE over polling** — subscribe to `/events` when app foregrounded; invalidate targeted query keys.
6. **Dedup** — TanStack Query `staleTime` 30 s for profiles/settings; 0 for operations.
7. **Bulk access** — single `POST /content-access/bulk`, never per-pair loops.
8. **Virtualisation** — add `@tanstack/svelte-virtual` only if profiling shows DOM > 200 nodes hurts scroll.

### Query key design

```
['device']
['library', { search, kind, available, profile_name, cursor }]
['media', mediaId]
['media', mediaId, 'access', profileName]
['operations']
['operation', operationId]
['tokens']
['token', uid]
['profiles']
['profile', name]
['profile', name, 'favorites', cursor]
['collections']
['media-sources']
['settings']
['playback']
```

### Profiling checklist

- [ ] Lighthouse on static build served locally
- [ ] Scroll test with mock 20k paginated responses
- [ ] Upload queue with 100 files (grouped UI, parallel limit 3)
- [ ] Search keystroke latency
- [ ] SSE reconnect behaviour

### Bundle strategy

- SvelteKit `adapter-static`, SPA fallback.
- Route-level code splitting: connect, library, tokens, profiles, device, settings.
- Uppy loaded only on upload routes / dynamic import.
- OpenAPI types: build-time generation, tree-shaken fetch wrapper.

---

## H — Component Architecture

Only primitives needed for v1 vertical slices. No speculative design-system package.

### Shell

| Component | Responsibility |
|---|---|
| `AppShell` | Breakpoint detection, nav slot, connection guard |
| `ConnectScreen` | URL + key form, validation |
| `ConnectionBanner` | Offline/reconnecting indicator |
| `NavSidebar` | Desktop navigation |
| `NavBottomBar` | Mobile tabs |
| `NavRail` | Tablet icon rail |
| `MoreMenu` | Mobile overflow |

### Library

| Component | Responsibility |
|---|---|
| `MediaGrid` / `MediaList` | Responsive layout, selection mode |
| `MediaCard` | Thumbnail, title, kind badge, availability |
| `MediaDetail` | Header, sections, actions |
| `ChapterList` | Read-only chapters |
| `LibraryToolbar` | Search, filters, sort, view toggle |
| `SelectionBar` | Bulk action bar |
| `AudienceEditor` | Shared/selected profiles toggle |
| `DropOverlay` | Desktop drag-and-drop |

### Upload

| Component | Responsibility |
|---|---|
| `UploadQueue` | Grouped progress (folder/heuristic) |
| `UploadFAB` | Mobile entry |
| `AddContentSheet` | Source picker (files; placeholders for podcast/radio/NAS) |

### Tokens

| Component | Responsibility |
|---|---|
| `TokenGrid` | Visual token → artwork → title |
| `TokenAssignWizard` | Capture → pick → confirm |
| `TokenWaitState` | Waiting animation |

### Profiles

| Component | Responsibility |
|---|---|
| `ProfileCard` | Avatar, name, level |
| `ProfileDetail` | Settings sections, favorites link |
| `ProfileAccessList` | Media visible for profile (`profile_name` filter) |

### Device & settings

| Component | Responsibility |
|---|---|
| `DeviceSummary` | Human status sentence |
| `StorageMeter` | Visual storage bar |
| `DiagnosticsPanel` | Progressive disclosure |
| `SettingsSection` | Grouped PUT form with restart notice |
| `SourceCard` | NAS/local source status |

### Primitives (shared)

| Component | Responsibility |
|---|---|
| `Button` | primary / secondary / ghost / danger |
| `IconButton` | accessible, 44 px touch |
| `Input`, `SearchInput` | with clear button |
| `Sheet` | mobile bottom sheet |
| `Dialog` | destructive confirm only |
| `Toast` | ephemeral feedback |
| `Skeleton` | loading placeholders |
| `EmptyState` | guided CTA |
| `ErrorState` | calm message + retry + details |
| `Avatar` | profile initials |
| `Badge` | kind, availability |
| `ProgressBar` | upload/operation |
| `Checkbox`, `Switch`, `Chip` | selection/filter |

### Lib modules

```
src/lib/
  api/client.ts       # generated types + fetch wrapper
  api/config.ts       # same-origin base URL; explicit loopback only in development
  api/errors.ts       # ErrorBody code mapping → DE messages
  queries/            # TanStack Query factories
  stores/connection.ts
  design/tokens.css
  utils/format.ts     # duration, bytes, dates
  upload/uppy.ts      # Uppy config, swappable transport
```

### Error message mapping (examples)

| `error.code` | User message (DE) |
|---|---|
| `authentication_required` | Bitte melde dich erneut an. |
| `password_incorrect` | Das Passwort ist nicht korrekt. |
| `auth_rate_limited` | Zu viele Versuche. Bitte versuche es in Kürze erneut. |
| `media_not_found` | Dieser Inhalt wurde nicht gefunden. |
| `token_not_detected` | Noch kein Token erkannt. Halte die Karte erneut an AQENO. |
| `upload_too_large` | Die Datei ist zu groß (max. 4 GB). |
| `bulk_limit_exceeded` | Zu viele Einträge auf einmal. Bitte in kleineren Gruppen versuchen. |

---

## Implementation order (vertical slices)

1. **Login / App Shell** — password/session auth, responsive nav, design tokens
2. **Library read** — infinite list, search, filter, detail pane
3. **Upload + ingestion progress** — Uppy, operation tracking, SSE
4. **Media detail/edit** — PATCH, artwork, delete
5. **Token assignment** — capture wizard, token grid
6. **Profiles + access** — audience editor, bulk access
7. **Sources** — read-only cards, scan trigger
8. **Podcast** — blocked UI + API Gap doc (no fake RSS)
9. **Radio** — blocked UI + API Gap doc
10. **Device / settings** — summary, diagnostics, settings PUT

---

## PWA recommendation

**Defer.** Installability is low effort with static manifest + icons, but offline editing is out of scope and the app requires local AQENO connectivity. Revisit when connect flow is stable; add manifest + `theme-color` only (no service-worker cache of API responses).

---

## Open decisions for human review

1. **Music filter** — two API calls vs. wait for G9?
2. **Profile creation** — hide until G5, or document „profiles configured on device“?
3. **Play button** — omit entirely (G11) or show informational „Am Gerät abspielen“?
4. **Default language** — follow `SettingsResource.language` or browser locale?

---

## Wireframe summaries

### Library — Desktop

```
[Sidebar]  [ Search……………………… ] [Filter▾] [⊞≡]     [+ Hinzufügen]
           ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
           │art │ │art │ │art │ │art │ │art │
           │    │ │    │ │    │ │    │ │    │
           └────┘ └────┘ └────┘ └────┘ └────┘
           … infinite scroll …
                                              ┌──────────────┐
                                              │ [artwork]    │
                                              │ Title        │
                                              │ Hörspiel·14  │
                                              │ Sichtbarkeit │
                                              │ Kapitel      │
                                              └──────────────┘
```

### Token assign — Mobile

```
┌─────────────────────────┐
│  ←  Token zuordnen      │
├─────────────────────────┤
│                         │
│      ((  NFC  ))        │
│                         │
│  Halte deine Karte      │
│  an AQENO               │
│                         │
│  ● ● ○  Schritt 1/3     │
└─────────────────────────┘
```

### Bulk access — Desktop

```
[3 ausgewählt]  [Für Profile freigeben] [Entfernen]
┌─────────────────────────────────────────┐
│ Freigeben für:                          │
│ [✓ Paul] [✓ Anna] [  Jens]              │
│            [ Übernehmen ]               │
└─────────────────────────────────────────┘
```

---

*Next step: scaffold `admin/` SvelteKit project and implement slice 1 (Connect / App Shell).*
