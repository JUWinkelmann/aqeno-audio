# ADR 0018 — Local Management API

**Status:** Accepted
**Date:** 2026-08-18
**Accepted:** 2026-08-18

## Context

ADR 0012 reserves a separate authenticated Management UI over application use cases. AQENO now
needs that boundary for local ownership: media import and correction, artwork, token assignment,
profiles/settings and useful device diagnosis must work without an AQENO cloud service. The contract
must also be sufficient for an independently developed client and libraries with tens of thousands
of files.

## Decision

AQENO exposes a versioned local HTTP adapter under `/api/v1`. FastAPI is used because it maps typed
request/response models to a machine-readable OpenAPI 3 contract, supports streamed multipart
uploads through Starlette, has straightforward in-process contract tests and does not move product
logic out of the application layer. Uvicorn is the production/development ASGI server.

The service is local-first and independently optional. Playback, physical input, NFC launch and the
Device UI never wait for HTTP readiness. The adapter consumes application services and immutable
snapshots; it never exposes SQLite rows, configuration files, filesystem browsing or Python domain
objects as JSON.

All management routes require a management key in `X-AQENO-Management-Key`. Cookie authentication is not used,
so browser ambient authority and CSRF are avoided; CORS is disabled by default. The development
server binds to loopback unless a Manager deliberately binds it to the LAN. A generated device key
is stored locally with owner-only permissions. This is the minimum prototype trust boundary, not an
account or OAuth platform.

Library lists use opaque cursors, bounded limits and stable `(normalised title, ContentId)` ordering.
List representations omit sources, chapters and original artwork bytes. Artwork has separate URLs.
Long-running scan/import work is represented by a small in-memory `Operation` application service;
it is not a durable or distributed job system. Server-Sent Events provide optional local change
notification while every event-producing resource remains readable through ordinary HTTP.

Media roots are OS-provided absolute directories. AQENO does not implement NFS/SMB protocols or NAS
discovery. A root unavailable at scan start is not scanned and, crucially, cannot make its indexed
works unavailable. Browsing uses the local SQLite index; audio paths are touched only during scan or
playback.

## Consequences

- Local management and its shipped assets require no internet or cloud account.
- OpenAPI is the client handover boundary and breaking changes require a new API version or an
  explicitly reviewed compatible migration.
- FastAPI, Starlette/Pydantic transitively, Uvicorn and python-multipart become runtime dependencies.
  Their licences and exact release versions must be retained in release compliance.
- The API key protects LAN mutation without inventing users. An authorised Manager may create a
  short-lived, single-use code to pair another local client. Certificate transport remains later
  security work before exposure beyond a deliberately trusted LAN.
- Avahi publishes the local HTTP endpoint. Wi-Fi/captive-portal setup, updates, messaging, Connect
  and remote access are not added by this decision.

## Rejected alternatives

**Direct calls from a web client into Python.** No independent client contract and no replaceable
presentation boundary.

**Cloud relay as the normal route.** Violates local ownership and makes the user's own device depend
on an external service.

**Flask plus handwritten OpenAPI.** Adds schema drift work without a product benefit.

**WebSocket-first event protocol.** Bidirectional state is unnecessary. SSE plus resource reads is
sufficient for token detection and operation completion.

**Unauthenticated trusted-LAN service.** Anyone on the WLAN could delete media or change a child's
volume ceiling.
