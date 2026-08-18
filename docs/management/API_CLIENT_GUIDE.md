# AQENO Local Management API Client Guide

This guide is for a client developer who does not need AQENO's Python code.

## Connection

- Development: `http://127.0.0.1:8766/api/v1`
- Product entry: `http://aqeno.local` (no port); same-origin API is `/api/v1`.
- Diagnostic fallback: `http://DEVICE_IP` when the client/network does not resolve mDNS.
- Appliance Uvicorn is loopback-only on `127.0.0.1:8766`; systemd exposes port 80.
- OpenAPI: `/api/openapi.json`; interactive development docs: `/api/docs`.

Browser clients call `/auth/status`, use the physical RH1 sequence Previous → Encoder → Next for
setup/recovery when required, and log in through `/auth/login`. Send cookies with
`credentials: include`; retain the returned `csrf_token` only for
the tab/session and send `X-AQENO-CSRF` on POST/PUT/PATCH/DELETE. Passwords are sent only to auth
routes and never retained by the client. `POST /auth/logout` invalidates the session.

The owner-only `management.key` header remains solely for diagnostic scripts and non-browser
compatibility. It is not a human login and must never be embedded in the Admin bundle.

## Development server

```bash
AQENO_CONFIG_DIR=/tmp/aqeno-api/config \
AQENO_DATA_DIR=/tmp/aqeno-api/data \
AQENO_STATE_DIR=/tmp/aqeno-api/state \
AQENO_MEDIA_DIR=/tmp/aqeno-api/media \
AQENO_MANAGEMENT_KEY=development-only \
.venv/bin/python -m aqeno.management --port 8766
```

The full AQENO process starts the adapter after playback readiness. `--no-management` exists to test
failure isolation.

For hot-reload development, Vite runs on `127.0.0.1:5173` and proxies its same-origin `/api` path to
the loopback API. AQENO additionally allows only the documented loopback development origins for
diagnostic direct calls; production uses same-origin static assets.
`npm run build` produces `admin/build`, which AQENO serves automatically. No Node process is needed
at runtime.

## Core flows

Diagnostic status using the break-glass machine credential:

```bash
curl -H 'X-AQENO-Management-Key: development-only' \
  http://127.0.0.1:8766/api/v1/device
```

Import:

```bash
curl -X POST -H 'X-AQENO-Management-Key: development-only' \
  -F 'file=@Story.mp3' http://127.0.0.1:8766/api/v1/imports
```

Poll `/operations/{id}` to `completed` or `failed`, then query
`/library/media?search=Story&limit=50`. Correct metadata with PATCH on the media resource and artwork
with multipart PUT on its `/artwork` resource.

Token assignment:

```text
POST /token-captures
GET  /token-captures/{id}                 until detected
PUT  /token-captures/{id}/assignment      {"media_id":"UUID"}
DELETE /token-captures/{id}                cancel and restore normal NFC playback
```

SSE can replace waiting polls, but GET the resource after an event. Once assigned, closing the
browser has no effect: AQENO Core owns the persisted mapping and subsequent playback.

For settings/profile edits, GET the complete typed resource, change known fields and PUT it back.
Responses currently state `apply_mode: restart_required`; clients must not claim immediate apply.

Physical controls are separate because availability and compatible gestures are device
capabilities. GET `/controls`, render the returned controls/events, and offer only actions whose
`compatible_events` contains that event. PATCH one mapping with `{"action_id": "..."}` (or `null`
for unassigned); POST `/controls/reset` restores only control defaults. Illumination accepts `off`,
`subtle` or `clear`. These changes are immediate and do not require a restart. Never hard-code that
all AQENO hardware has two buttons or a pressable encoder, and never expose the internal settings
encoding.

Profiles are local listening contexts, never login identities. Use `profile_name` on library queries
so filtering remains server-side. Favorites live below `/profiles/{name}/favorites`; resume for a
work is read below `/profiles/{name}/progress/{media_id}`.

For visibility changes use one `POST /content-access/bulk`, not one request per media/profile pair:

```json
{
  "media_ids": ["MEDIA_UUID", "MEDIA_UUID"],
  "operation": "set_selected_profiles",
  "profile_names": ["anna", "paul"]
}
```

Operations are `set_shared`, `set_selected_profiles`, `allow`, `deny` and `clear_override`.
Collections provide inherited access for groups. Read
`/library/media/{media_id}/access/{profile_name}` when an administration view must explain whether
the result is explicit, inherited or the shared default.

## Large-library rules

1. Never request or mirror the full library.
2. Load `limit=50`, follow `next_cursor`, and never parse/construct cursors.
3. Send search/filter input to the server after a short debounce.
4. Fetch MediaDetail only when opening a work; lists intentionally omit chapters/sources.
5. Load `artwork_thumbnail_url`; no list contains Base64 artwork.
6. Refresh an affected object/page after mutations or SSE, not every screen globally.
7. Treat media UUID as identity; source names/paths may change.
8. Keep unavailable works visible and never infer deletion from an offline source.

## Errors, events and generation

Errors are `{ "error": { "code", "message", "details" } }`; branch only on code. `401` requires
login or reports an incorrect password, `403` reports missing CSRF, `404` unknown resource, `409`
workflow state, `413` upload size, `429` temporary login throttling and `422` schema/product policy.

`GET /events` is authenticated SSE. v1 events are `operation.changed`, `token.capture_changed` and
`playback.changed`. Polling remains fully supported.

Live physical-control highlighting is not a v1 event. The current Admin confirms a saved mapping and
the user tests it at the device; adding input telemetry requires a bounded explicit contract rather
than leaking the local input stream.

Use [openapi.json](./openapi.json) as source of truth. A generated TypeScript type/client package is
a useful separate artifact; generated code is disposable and must not replace OpenAPI. Preserve UUID
strings and enum strings; browser authentication is cookie/CSRF based.

Not supported: cloud/remote access, accounts, messages, updates, Wi-Fi mutation, NAS
discovery/mounting, chapter editing, arbitrary filesystem browsing or raw log download.
