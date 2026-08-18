# ADR 0012 — Device UI and management UI are separate presentations

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

ADR 0002 selects Qt 6, PySide6 and Qt Quick/QML for the display on AQENO Reference Hardware. It
does not distinguish that appliance UI from the substantially broader administration needed for
content, NFC assignments, network configuration and possible future services.

Putting both concerns into QML would enlarge the child-facing device experience and make QML a
second application layer. Making all management call internal Python objects directly would instead
prevent a later responsive management client without moving product rules again.

## Decision

AQENO has three responsibilities with explicit boundaries:

1. **Core/Application** owns product behaviour: playback, library and resume rules, NFC actions,
   authorisation, capability availability and hardware-independent state.
2. **Device UI** is the in-process Qt Quick/QML appliance surface selected by ADR 0002. QML owns
   presentation, layout, touch interaction and short, calm visual transitions. It presents state and
   emits user intentions; it does not reproduce Core decisions.
3. **Management UI** is a separate adult-facing presentation. A responsive web client is permitted
   later, but no framework, protocol, listener or API is selected or implemented by this ADR.

For the Device UI, concrete Python view models in `ui/models/` are the presentation boundary. They
expose already-decided state and available actions as Qt properties/signals and call application use
cases for user intentions. QML does not inspect persistence, adapters, network state, subscription
state or hardware directly. No generic UI framework interface is introduced.

The Device UI builds navigation and actions from available capabilities. An unavailable capability
contributes no surface; disabled paid controls, locks, tier badges and upgrade prompts are forbidden
by Product Principle P15.

Complex administration does not belong on the box. The local `SETUP` state remains for bounded
appliance tasks such as pairing, recovery and simple choices. It is not the permanent home for
media management, NFC assignment, account management or service configuration.

A Management API is a presentation adapter over application use cases. ADR 0018 selects the local,
authenticated implementation. It may not expose persistence or other internal Python objects as its
contract. Future remote access remains a separate adapter/transport decision and cannot become a
gateway required to operate the local device.

Qt Virtual Keyboard is not part of the AQENO product runtime. Device flows avoid complex free-text
entry; no replacement keyboard is implemented. This is a product-scope decision as well as avoiding
the module's GPLv3/commercial licensing constraint. Reconsideration requires a concrete local-entry
need and a new dependency/licensing review.

## Consequences

The Core remains free of PySide6 and QML and can support another OEM presentation without a Core
rewrite. The Device UI stays small and appliance-like: fullscreen, no desktop chrome or classical
dialogs, large touch targets, little text, reduced navigation and no visual activity competing with
audio. `DEVICE_UI_PRINCIPLES.md` is the product contract for that simplicity; this ADR defines where
the decisions behind it live.

ADR 0002's in-process decision applies to the Device UI. It rules out an IPC layer between QML and
the Core; it does not rule out a future authenticated Management API as a separate presentation.

PySide6/Qt modules must be reviewed individually before distribution. PySide6 and the Qt modules
used by the Device UI must remain dynamically linked and replaceable where LGPL terms are relied on;
licence texts and exact module versions belong in release compliance. Qt Virtual Keyboard remains
excluded. **Legal review required** before proprietary distribution.

The first Device UI needs concrete view models only when its QML contract exists. Creating them now
would invent properties and actions ahead of the vertical slice; this ADR supplies the boundary they
must follow.

## Alternatives considered

**Put administration into the QML application.** Rejected because it turns an audio appliance into
a general settings application and couples adult workflows to the Reference display technology.

**Use a web UI for both device and management.** Rejected for the Device UI by ADR 0002's measured
boot/display-control concerns. It remains suitable for later management because that surface has
different constraints.

**Define a generic presentation port now.** Rejected as speculative. Concrete application use cases
and view models provide the required boundary without pretending all future UIs share one framework
contract.
