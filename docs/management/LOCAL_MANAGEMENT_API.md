# AQENO Local Management API Blueprint

**Status:** Canonical local API contract
**Version:** `/api/v1`
**Date:** 2026-08-18

## Architectural rule

> Anything required to own and operate your AQENO belongs on AQENO. Cloud adds reach, not ownership.

The Management API is a replaceable presentation adapter over AQENO application use cases. The
Device UI, playback, physical controls and NFC playback do not call HTTP and remain operational when
the API, LAN or client is absent. The API and future clients share the one SQLite library, settings
store and application services with the Device UI; there is no web-only library or configuration.
When `admin/build/index.html` exists, the same adapter serves the replaceable static Admin SPA at
`/`. Node/Vite remains build-time tooling and is not a runtime service.

FastAPI/Uvicorn implement the HTTP/OpenAPI boundary (ADR 0018). API DTOs in `management/schemas.py`
are separate from domain values. Stable content UUIDs cross the boundary; paths, SQLite row IDs,
mutagen objects, tracebacks and live Python objects do not become identity.

## Phase 1 audit

| Area | Existing before this change | Management conclusion |
|---|---|---|
| library | stable `ContentId`, work/chapter/source distinction, SQLite | expose media objects; add indexed cursor query |
| ingestion | grouping, fingerprints, stable identity, incremental fields | expose bounded scan/import operation; skip unchanged works |
| external media | absolute configurable roots, unavailable content state | OS mounts remain roots; preserve index if root itself is unavailable |
| metadata/artwork | fields persisted; artwork path internal | application mutations plus separate authenticated binary endpoint |
| tokens | stable UID → `ContentId` persistence and `NfcPresented` | add capture/assignment use case; no manual UID requirement |
| playback | immutable snapshot and listeners | read-only status; remote control is not a current use case |
| profiles/settings | User/Manager/Owner, validated TOML, display/volume policies | typed resource; no raw TOML; current application requires restart |
| readiness/display | application snapshots | expose product status, not Linux internals |
| diagnostics | health/failure vocabulary exists | bounded status; no raw log download |
| API | ADR 0012 boundary only | new versioned local FastAPI adapter and OpenAPI |

True gaps closed here are server-side library queries, management use cases, async operation state,
token capture, API authentication/error shapes, incremental unchanged-file scans and non-destructive
offline-root scans. Chapter editing, updates, network mutation and
durable operation history remain explicit gaps rather than invented behaviour.

## Resource model

- **Device**: stable device ID, AQENO version, readiness, useful capabilities and storage capacity.
- **Diagnostic**: bounded component health and stable AQENO failure codes.
- **MediaSource**: configured local or OS-mounted root and reachability; never an SMB/NFS account.
- **MediaObject**: one AQENO work. List shape is compact; detail contains chapters and source summaries.
- **Artwork**: authenticated binary representation referenced by URL, never Base64 in a list.
- **Operation**: process-local import or scan with `queued | running | completed | failed`.
- **TokenCapture**: temporary `waiting | detected | assigned` setup interaction.
- **Token**: technical UID and optional media assignment for Manager use.
- **Playback**: read-only current snapshot.
- **Settings/Profile**: typed product policies with `restart_required`; never file contents.
- **Profile state**: per-profile favorites and resume; profiles are listening contexts, not accounts.
- **Audience/Collection**: shared-default visibility, selected-profile audiences, inherited group
  rules and explicit media exceptions (ADR 0019).
- **Event**: SSE hint; clients always re-read the named resource after an event.

## Endpoint inventory

`SESSION` means a valid HttpOnly Admin session; mutating requests additionally require
`X-AQENO-CSRF`. OpenAPI declares the `AdminSession` cookie security scheme; password fields are
write-only. The hidden Management key remains a break-glass machine path and is deliberately not
part of generated browser auth types. Every implemented route is in OpenAPI; errors use one envelope.

| Method | Path | Purpose | Request / response | Mapping | Auth | Errors | Status |
|---|---|---|---|---|---|---|---|
| GET | `/api/v1/auth/status` | setup/session state | — / AuthStatus | AdminAuth | public | — | IMPLEMENTED |
| POST/GET | `/api/v1/auth/setup/confirmations[/id]` | begin/poll physical ownership | — / Confirmation | AdminAuth + InputBus | public, physical | expired | IMPLEMENTED |
| POST | `/api/v1/auth/setup` | set first password/session | password + confirmation / Session | AdminAuth | physical | policy/state | IMPLEMENTED |
| POST | `/api/v1/auth/login` | password login | password / Session | AdminAuth | public | password/rate | IMPLEMENTED |
| POST | `/api/v1/auth/logout` | invalidate session | — / 204 | AdminAuth | SESSION+CSRF | auth | IMPLEMENTED |
| POST | `/api/v1/auth/password` | change password | current/new / Session | AdminAuth | SESSION+CSRF | password/policy | IMPLEMENTED |
| POST/GET | `/api/v1/auth/recovery/confirmations[/id]` | begin/poll local recovery | — / Confirmation | AdminAuth + InputBus | public, physical | expired | IMPLEMENTED |
| POST | `/api/v1/auth/recovery` | reset password/session | password + confirmation / Session | AdminAuth | physical | policy/state | IMPLEMENTED |
| GET | `/api/v1/device` | device/readiness/storage | — / `DeviceStatus` | Readiness, Library health | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/diagnostics` | bounded diagnosis | — / `DiagnosticsStatus` | snapshots/health | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/media-sources` | roots/mount availability | — / `MediaSource[]` | LibrarySettings | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/library/media` | indexed browse/search | cursor/filter / `MediaPage` | Library query | SESSION | cursor | IMPLEMENTED |
| GET | `/api/v1/library/media/{media_id}` | work detail/resume | profile / `MediaDetail` | Library/get_resume | SESSION | not found | IMPLEMENTED |
| PATCH | `/api/v1/library/media/{media_id}` | correct metadata | `MediaPatch` / detail | update_metadata | SESSION | validation | IMPLEMENTED |
| DELETE | `/api/v1/library/media/{media_id}` | remove AQENO object | — / 204 | remove_content | SESSION | not found | IMPLEMENTED |
| GET | `/api/v1/library/media/{media_id}/artwork` | artwork bytes | — / binary | artwork reference | SESSION | not found | IMPLEMENTED |
| PUT | `/api/v1/library/media/{media_id}/artwork` | replace artwork | multipart / detail | asset store | SESSION | type/size | IMPLEMENTED |
| DELETE | `/api/v1/library/media/{media_id}/artwork` | remove artwork | — / detail | set_artwork | SESSION | not found | IMPLEMENTED |
| POST | `/api/v1/imports` | upload and ingest | multipart / Operation 202 | ingestion | SESSION | size/name | IMPLEMENTED |
| POST | `/api/v1/library/scans` | scan roots | — / Operation 202 | ingestion | SESSION | operation | IMPLEMENTED |
| GET | `/api/v1/operations` | current operations | — / `Operation[]` | registry | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/operations/{operation_id}` | operation status | — / Operation | registry | SESSION | not found | IMPLEMENTED |
| GET | `/api/v1/tokens` | assigned tokens | — / `Token[]` | tag mappings | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/tokens/{uid}` | token assignment | — / Token | resolve_tag | SESSION | not found | IMPLEMENTED |
| DELETE | `/api/v1/tokens/{uid}/assignment` | unassign | — / 204 | unmap_tag | SESSION | auth | IMPLEMENTED |
| POST | `/api/v1/token-captures` | wait for token | — / capture 201 | TokenAssignment | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/token-captures/{capture_id}` | detection status | — / capture | TokenAssignment | SESSION | not found | IMPLEMENTED |
| DELETE | `/api/v1/token-captures/{capture_id}` | cancel capture | — / capture | TokenAssignment | SESSION | not found | IMPLEMENTED |
| PUT | `/api/v1/token-captures/{capture_id}/assignment` | assign detected token | media ID / capture | map_tag | SESSION | state/media | IMPLEMENTED |
| GET | `/api/v1/playback` | playback snapshot | — / PlaybackStatus | PlaybackSession | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/settings` | local settings | — / Settings | SettingsStore | SESSION | auth | IMPLEMENTED |
| PUT | `/api/v1/settings` | validate/persist settings | Settings / Settings | validate/store | SESSION | range | IMPLEMENTED |
| GET | `/api/v1/profiles` | configurations | — / Profile[] | Library profiles | SESSION | auth | IMPLEMENTED |
| GET | `/api/v1/profiles/{name}` | one profile | — / Profile | Library | SESSION | not found | IMPLEMENTED |
| PUT | `/api/v1/profiles/{name}` | persist policies | Profile / Profile | domain values | SESSION | policy | IMPLEMENTED |
| DELETE | `/api/v1/profiles/{name}` | remove local context | — / 204 | ConfigurationManagement | SESSION | not found | IMPLEMENTED |
| GET | `/api/v1/profiles/{name}/favorites` | paged personal favorites | cursor / MediaPage | Library index | SESSION | not found | IMPLEMENTED |
| PUT/DELETE | `/api/v1/profiles/{name}/favorites/{media_id}` | set/unset favorite | — / Favorite | ProfileContentManagement | SESSION | not found | IMPLEMENTED |
| GET | `/api/v1/profiles/{name}/progress/{media_id}` | personal resume | — / Progress | Library resume | SESSION | not found | IMPLEMENTED |
| POST | `/api/v1/content-access/bulk` | many-media/many-profile access | BulkAccess / result | ProfileContentManagement | SESSION | limits/IDs | IMPLEMENTED |
| GET | `/api/v1/library/media/{media_id}/access/{profile}` | explain effective access | — / EffectiveAccess | indexed policy | SESSION | not found | IMPLEMENTED |
| GET/POST | `/api/v1/collections` | list/create access grouping | Collection / Collection | Library | SESSION | validation | IMPLEMENTED |
| PUT/DELETE | `/api/v1/collections/{collection_id}` | replace/remove grouping | Collection / Collection | Library | SESSION | not found | IMPLEMENTED |
| PUT | `/api/v1/collections/{collection_id}/audience` | inherited audience | Audience / Collection | ProfileContentManagement | SESSION | profiles | IMPLEMENTED |
| GET | `/api/v1/events` | local change hints | — / SSE | listeners | SESSION | auth | IMPLEMENTED |
| GET | `/api/openapi.json` | machine contract | — / OpenAPI | FastAPI | public | — | IMPLEMENTED |
| GET | `/api/docs` | development viewer | — / Swagger UI | OpenAPI | public | — | IMPLEMENTED |
| PATCH | chapter structure | manager override | — | no override contract | — | — | CONTRACT ONLY / NOT INCLUDED |
| PUT | network configuration | configure Wi-Fi | — | no network port | — | — | CONTRACT ONLY / NOT INCLUDED |
| POST | updates | install update | — | no update model | — | — | FUTURE / NOT INCLUDED |
| any | Connect/messages/remote/accounts | internet convenience | — | future concepts | — | — | FUTURE / NOT INCLUDED |
| any | local backup/restore | appliance recovery | — | local engine exists; HTTP contract does not | — | — | API GAP / NOT INCLUDED |

Deleting a media object removes its AQENO index identity, token assignments and resume state through
existing persistence semantics. It does not currently delete arbitrary source files. That destructive
storage policy needs a separate decision.

## List and scale contract

- `limit` defaults to 50 and is bounded to 1–100.
- `cursor` is opaque; ordering is stable by case-folded title and media UUID.
- `search`, `kind`, `available` and `profile_name` execute in SQLite, not in the client.
- `total` applies before the cursor; `next_cursor` remains paging authority.
- list items omit chapters/sources and contain an artwork URL, never image bytes.
- ordinary browse never stats media files or contacts a NAS.

SQLite indexes cover title/order, kind/availability, resume recency, fingerprint, member path and
token lookup. The model is appropriate for tens of thousands of files/media members, not a
multi-node or million-item claim.

## Profile and effective-access contract

Profiles never authenticate. Favorites and resume are personal; media identity and source records
remain shared. The default is `shared`, so a new profile sees an existing shared library without
thousands of assignments. `selected_profiles` restricts a media object or collection. Explicit
per-media `allow`/`deny` overrides collection inheritance; a media audience applies when no
audience-bearing collection does. Device browse, search, touch selection, favorites, resume and NFC
all enforce the effective result. The Device UI omits denied media.

`POST /content-access/bulk` supports `set_shared`, `set_selected_profiles`, `allow`, `deny` and
`clear_override` for up to 1,000 media and 50 profiles atomically. Collection changes express a
single decision for many members. Administrative access detail identifies explicit, inherited and
effective state without inflating normal list responses.

## Import, scan and external source contract

Uploads are multipart, streamed from `UploadFile` to an adjacent temporary file, fsynced and
atomically renamed. Media limit is 4 GiB; artwork limit is 20 MiB. Media upload returns `202` and an
Operation. Scanning runs on a dedicated single worker and commits one work at a time; playback never
waits for it. Unchanged files match stored path/size/mtime and skip probing; changed/moved files use
the existing payload fingerprint identity.

An NFS/SMB directory is mounted by the OS and configured as an absolute root. AQENO does not know the
network protocol. If the root itself is absent, its works are excluded from the scan's unavailable
comparison, retaining local identity, metadata, artwork, token assignment and resume. AQENO does not
discover NAS devices, manage credentials, mount protocols, copy audio, transcode or administer
storage.

## Error contract

```json
{"error":{"code":"media_not_found","message":"...","details":null}}
```

Clients branch on `code`, never message. No traceback crosses HTTP. Principal codes:
`authentication_required`, `password_incorrect`, `auth_rate_limited`, `csrf_required`,
`physical_confirmation_required`, `password_policy`, `validation_failed`, `cursor_invalid`, `media_not_found`,
`artwork_not_found`, `artwork_type_unsupported`, `upload_filename_missing`, `upload_too_large`,
`operation_not_found`, `operation_failed`, `token_not_found`, `token_capture_not_found`,
`token_not_detected`, `settings_out_of_range`, `profile_not_found`, `profile_name_mismatch` and
`profile_policy_invalid`, plus stable playback failure codes inside playback status.
Access additions are `bulk_limit_exceeded`, `collection_not_found` and `profiles_required`.

## Authentication and local threat model

ADR 0022 is authoritative. A local scrypt password plus the 90-second physical sequence Previous →
Encoder → Next owns setup/recovery. Random server-side sessions use HttpOnly, SameSite=Strict cookies; every mutation
made through a session requires its separate CSRF token. Password change/recovery revokes all older
sessions. Five failed logins begin a bounded increasing delay, never permanent lockout. Profiles do
not authenticate.

Reference production is `http://aqeno.local`: port 80 is a systemd socket proxy to Uvicorn bound only
to `127.0.0.1:8766`. Development may use direct loopback. Exact Vite origins alone receive credentialed
CORS. The 0600 Management key remains hidden break-glass/machine authority and never appears in normal
UI/OpenAPI auth DTOs. Plain HTTP supports a trusted LAN only; it does not resist passive LAN capture.

## Events, process isolation and versioning

SSE types are `operation.changed`, `token.capture_changed` and `playback.changed`. Events are lossy
hints; clients re-read resources and can always poll. No WebSocket command bus is introduced.

The standard AQENO process starts the adapter after `PLAYBACK_READY`; startup failure is optional
degradation. Uvicorn and scan work run away from the playback path. The standalone
`python -m aqeno.management` target supports client development but reports unavailable live
components honestly.

Compatible additions may remain in v1. Removed/renamed fields or changed meanings require deliberate
review and normally `/api/v2`. `docs/management/openapi.json` is authoritative. No v1 path is
reserved for Connect, remote/cloud access, accounts, subscriptions, messages or OEM. Local backup
and restore remain a separately documented Appliance API gap rather than a cloud feature.
