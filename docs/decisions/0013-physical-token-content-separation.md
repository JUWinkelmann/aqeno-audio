# ADR 0013 — Physical tokens identify AQENO assignments, not content sources

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

AQENO supports physical objects carrying compatible NFC tags. Such an object may be a card,
sticker, key ring, self-made figure or an otherwise compatible object from a third party. The
object's shape, brand and original product category do not change what AQENO needs from it: a stable
identifier that can launch an AQENO-owned assignment.

Without an explicit boundary, physical recognition could become coupled to content acquisition or
invite manufacturer-specific domain objects. That would contradict `Content != Source != Trigger`,
open content and the rule that NFC is a shortcut rather than a content store.

## Decision

The existing model is sufficient and remains unchanged:

- `NFCTag` is the current NFC trigger concept; `tag_id`/UID is its opaque identifier.
- `TagMapping` stores an AQENO-local assignment to a `ContentId` in the current slice. When Actions
  are implemented, the documented domain permits a tag to target an Action without changing the
  token's identity.
- `ContentItem` and its Sources remain independent from the tag and assignment.

No `PhysicalToken`, manufacturer product or brand-specific domain class is added. `Trigger` remains
the broader domain term; NFC is the concrete identification technology currently in scope.

Recognising a tag performs only the AQENO-local lookup. It never implies that AQENO should discover,
download, extract or decrypt content associated with the same object in another system. The mapped
target must already be legitimately available to AQENO through its ordinary Sources.

Technically compatible third-party objects may be read like any other compatible tag, without a
brand integration or compatibility claim. Advertising compatibility with a named product, using a
third-party service or implementing a proprietary protocol requires a separate product and legal
decision.

Assignment belongs in the adult Management UI described by ADR 0012. Normal Device UI and Kids UI
do not expose the technical UID; the child interaction remains presenting an object and hearing its
assigned content.

## Alternatives considered

**Introduce `PhysicalToken -> Assignment -> MediaTarget` as new types now.** Rejected because the
existing `NFCTag`, tag mapping, `ContentId`, Action and Trigger concepts already express those roles.
Duplicating them would create terminology without behaviour.

**Model recognised third-party products by brand.** Rejected because AQENO uses only the compatible
identifier. A product-specific type would imply semantics, content access or support that does not
exist.

**Resolve content from the physical identifier automatically.** Rejected because identification and
content sourcing are independent. It would couple Core playback to proprietary systems and could
cross technical-protection, contractual or copyright boundaries.

## Consequences

Any compatible NFC carrier can participate without changing Core or media identity. Reassigning or
deleting a tag mapping cannot delete content or resume state, as already enforced by persistence
contract tests.

AQENO gains no ability to use content merely because it recognises an object. Content import,
provider integration and rights remain separate decisions with their own provenance and licensing
requirements.

This ADR does not settle the remaining reader-level details in gap G21, including canonical UID
format and debounce behaviour on physical hardware.
