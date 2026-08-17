# AQENO Domain Model

## Core separation
`Content != Source != Presentation != Trigger`

A media item is not defined by where it came from, how it is shown, or how playback was triggered.

## Initial entities/value objects

### ContentItem
Stable AQENO identity, title, optional artwork, content kind, duration/stream semantics, availability and metadata.

### Source
Resolvable origin for a ContentItem: local file, HTTP stream, podcast enclosure, future provider.

### Collection
Ordered or semantic grouping of ContentItems.

### PlaybackState
Current content identity, source resolution, position, queue/context and transport state.

### Profile
User-facing capability and presentation configuration.

### Role
`User`, `Manager`, `Owner`.

### Action
Semantic command such as PlayContent, OpenCollection, ActivateScene or SwitchProfile.

### Scene
Named bundle of policies/actions such as Sleep or Travel.

### NFCTag
Brand-neutral NFC identifier mapped to an AQENO-local target. The current slice maps directly to a
`ContentId`; Actions may become targets when implemented. The tag does not own content and conveys
nothing about its Source (ADR 0013).

### DisplayPolicy
Rules controlling display state transitions, timeouts, brightness/LED behaviour and allowed Ambient behaviour.

### Device
Logical AQENO instance and its capabilities.

### Capability
Declared support such as touch, NFC, physical inputs, controllable LEDs, audio output or battery telemetry.

## Invariants
- playback progress belongs to content/profile context, not to an NFC tag;
- deleting/replacing a tag must not delete content;
- recognising a tag never resolves or acquires content outside its AQENO-local assignment;
- UI representation is derived from Profile + Content metadata;
- hardware adapters emit semantic inputs and never mutate domain state directly;
- cloud/provider identifiers may be attached to Sources but must not become AQENO's primary identity.
