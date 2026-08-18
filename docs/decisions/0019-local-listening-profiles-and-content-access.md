# ADR 0019: Local listening profiles and content access

**Status:** Accepted
**Date:** 2026-08-18

## Decision

Profiles are local listening contexts, not accounts or authentication identities. Management
authorization remains the separate local Admin trust boundary described by ADR 0018 and amended by
ADR 0022. Media identity is shared; favorites and playback progress are stored per profile.

Content is shared by default. A media object may instead name selected profiles. A minimal
collection groups media for one inherited audience, and an explicit media/profile allow or deny is
the exception mechanism. Effective access uses this precedence:

1. explicit media/profile override;
2. any audience-bearing collection containing the media;
3. the media audience;
4. shared default.

If multiple audience-bearing collections contain a medium, any granting collection grants access.
An explicit media deny still wins. Every launch path uses the same effective policy; unavailable
content is absent from the Device UI rather than shown locked.

Bulk changes accept many media and many profiles in one transaction. The v1 safety bound is 1,000
media and 50 profiles per request. Profile-filtered library queries evaluate access in SQLite.

## Consequences

- A new profile does not require assignments for an existing shared library.
- Collection membership is introduced only for shared access administration, not as a second media
  library, playlist engine or generic taxonomy.
- No username, profile password, email, profile login, OAuth, cloud identity, RBAC or policy engine
  is introduced. The one local Administration password is outside the listening-profile model.
- Existing resume rows already contain a profile name; there is no destructive progress migration.
- There were no persisted favorites or visibility rules before this decision, so shared default
  preserves all existing content visibility.
