# ADR 0022 — Local administration entry and human trust

**Status:** Accepted
**Date:** 2026-08-18
**Amends:** ADR 0018 authentication and reference-network exposure

## Context

ADR 0018's generated Management key is a sound machine credential but an unacceptable human login.
The static Admin client and API already share one FastAPI origin, while the reference service exposes
its development port directly. AQENO needs password-based local ownership, cloud-free recovery and a
friendly URL without weakening LAN mutation protection or making listening profiles identities.

## Decision

The human-facing administration uses one local Admin password, not an account. It is stored as a
versioned scrypt hash with a random salt; plaintext is never persisted or logged. Passwords require
10 characters, allow passphrases and impose no character-class or rotation rules.

First setup and password recovery require a 90-second physical confirmation. Reference Hardware 1
uses the deliberate sequence Previous → Encoder → Next because the current semantic input contract
has no reliable long-press event and a routine Play/Pause press must not accidentally transfer
ownership. Repeated network requests cannot replace a still-active challenge. The confirmation is
single-use. A future long-press may replace it only after the hardware port can represent it
deterministically.

Successful login creates a random server-side, 12-hour session. The browser receives only an
HttpOnly, SameSite=Strict cookie and a separate CSRF token for mutating requests. Sessions are
process-local, support multiple browsers, expire, and are all revoked by password change/recovery.
Login has a temporary increasing per-peer delay after five failures, never a permanent lockout.

The existing Management key remains a hidden, owner-only break-glass/machine credential for local
diagnosis, compatibility and headless confirmation of a setup/recovery challenge. It is not returned
by OpenAPI authentication routes, embedded in the Admin bundle, or entered in normal UI. The old
key-transfer pairing endpoints are removed.

Admin credentials and sessions are separate from listening profiles. Repair preserves the credential
because AQENO-DATA remains. Complete factory reset removes credential, sessions and bootstrap
ownership. Portable state backup excludes the device-local credential; after cross-device restore,
physical setup establishes new local administration. This deliberately avoids transporting an
offline password-verifier and old device authority.

Reference Platform 1 sets the mDNS hostname `aqeno` and advertises `aqeno.local`. The AQENO process
binds `127.0.0.1:8766`; a systemd socket proxy exposes the same UI/API origin on LAN port 80. Avahi
announces `_http._tcp` and `_aqeno-admin._tcp`. No `network-online.target` dependency is introduced.
Avahi conflict renaming handles multiple default-named devices; configurable friendly naming is
later work.

RH1 uses plain HTTP on a deliberately trusted LAN. SameSite/CSRF prevent browser cross-origin
mutation but HTTP does not prevent a hostile LAN participant from observing credentials or sessions.
A self-signed certificate with a browser warning is rejected as normal UX. WebAuthn/passkeys and
Secure cookies require a trustworthy HTTPS design and remain unavailable until local certificate
provisioning can avoid warnings.

## Consequences

- The normal journey is `http://aqeno.local` → physical confirmation/setup or password → Admin.
- The user never needs an IP, port, terminal or Management key.
- Development keeps direct loopback port 8766 and the break-glass header for automated clients.
- Sessions are invalid after AQENO restarts; re-login is required, while the password remains.
- If mDNS is unavailable, direct device IP on port 80 is the documented recovery path; port 8766 is
  loopback-only on the appliance.
- Passive attackers on an untrusted LAN remain outside the supported RH1 threat model. Remote access
  must not reuse this HTTP boundary.

## Alternatives considered

Argon2id was preferred cryptographically, but Python's maintained standard-library scrypt provides a
memory-hard password KDF without adding a native appliance dependency. JWTs were rejected because
server-side revocation is simpler. A new nginx/Caddy service was rejected because FastAPI already
serves both surfaces and systemd socket proxying removes the port without another package/config
stack. Binding Python directly to port 80 was rejected because it would expose the backend process
and require a low-port capability. Self-signed HTTPS was rejected because the warning teaches users
to bypass trust errors.
