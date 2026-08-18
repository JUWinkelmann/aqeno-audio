# AQENO Roadmap

This roadmap is discovery-led. Dates are intentionally omitted until the MVP is validated. The
current validation focus on Kids and Easy describes discovery contexts, not separate product cores;
the shared platform boundary is defined in `PRODUCT_FOUNDATION.md`. Unscheduled concepts in
`docs/product/FUTURE_PRODUCT_CONCEPTS.md` do not alter these phases or priorities.

## Current position

The project deliberately has an implemented First Vertical Slice before completing the broader P1
discovery programme. Desktop architecture and behaviour are proven; current progress is gated by
physical RH1 assembly and measurements. The phase lists below retain the broader discovery horizon,
but unchecked historic spike items do not mean the implemented slice is absent.

## P0 — Product foundation

- [x] Establish product position and principles.
- [x] Define adaptive UX direction.
- [x] Establish physical-vs-touch interaction principle.
- [x] Establish dark-room requirement.
- [x] Establish open NFC and hardware philosophy.
- [x] Establish one shared platform across Kids, independent and assisted use contexts.
- [ ] Complete core user journeys.
- [x] Identify product risks and open questions.

## P1 — UX discovery

- [ ] Journey: three-year-old / first setup through bedtime.
- [ ] Journey: beginning reader.
- [ ] Journey: independent older child.
- [ ] Journey: Guardian/Manager.
- [ ] Journey: independent Easy user.
- [ ] Journey: remotely assisted Easy user.
- [ ] Derive required physical controls.
- [ ] Derive adaptive UI capability matrix.
- [ ] Produce low-fidelity interactive prototype.
- [ ] Test prototype with representative users.

## P2 — Feasibility spikes

- [ ] Validate the accepted GStreamer audio path on assembled RH1.
- [ ] UI stack validation on Raspberry Pi 4 reference prototype.
- [ ] Display sleep/wake + dark-room spike.
- [ ] Validate the implemented rotary encoder/NeoKey adapter on assembled RH1.
- [ ] NFC spike.
- [ ] Podcast/RSS + local file content spike.
- [ ] Power-bank compatibility constraints.
- [ ] Alternative SBC evaluation.
- [ ] Licensing/commercial-distribution review of candidate dependencies.

## P3 — MVP definition

Freeze only after P1/P2 evidence.

**Amended 2026-08-18 (ADR 0015).** The evidence that currently counts is real use of the reference
prototype by its actual user, recorded in `docs/product/USE_OBSERVATIONS.md`. Prototype testing with
representative users in P1 belongs to the design horizon and to productisation; it does not gate the
first device. P5 remains the separate productisation phase, and nothing in it shapes decisions
today.

Expected MVP themes:

- local audio;
- podcast/RSS;
- compatible stream/radio playback;
- unified library;
- reliable resume;
- physical volume/play/pause/previous/next;
- screen-off playback and Dark Room;
- basic NFC mapping;
- Kids Early experience;
- local Manager/Owner setup and configuration.

## P4 — Alpha implementation

- [x] Hardware abstraction.
- [x] Content domain and storage.
- [x] Playback application layer.
- [x] Bounded Kids Early Device UI over adaptive architecture.
- [x] Versioned local Management API and OpenAPI handover.
- [ ] Local Management Web client integration and RH1 validation.
- [ ] NFC Actions.
- [ ] Scenes.
- [x] Reference systemd/Avahi installation path.
- [ ] Signed update and rollback path.

## P5 — Productisation exploration

- [ ] Reference DIY bill of materials.
- [ ] Printable enclosure.
- [ ] Reference / Compatible / Community hardware specification.
- [ ] Security review.
- [ ] Privacy/data review.
- [ ] Commercial hardware BOM study.
- [ ] Open-source/commercial licensing decision.
- [ ] Optional remote-management/cloud business case.


## Cross-cutting validation tracks

### Startup / wake performance
- Establish boot timing instrumentation on Reference hardware.
- Validate staged readiness: controls → local state → playback → UI → network.
- Set and monitor the Reference targets from `PRODUCT_FOUNDATION.md`.
- Prefer optimisation that improves perceived readiness without coupling the core to a single SBC.

### Display behaviour
- Prototype `OFF`, `DIM`, `INTERACTIVE`, `AMBIENT` and `SETUP`.
- Test Kids playback with automatic transition to visual quiet.
- Test full dark-room interaction without display wake.
- Prototype an opt-in digital photo-frame scene.
- Validate who may enable Ambient and select visual sources for Kids, Easy and Standard profiles.
- Reject attention-seeking transitions or automatic idle content that conflicts with audio-first use.
