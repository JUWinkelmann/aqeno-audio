# AQENO Roadmap

This roadmap is discovery-led. Dates are intentionally omitted until the MVP is validated.

## P0 — Product foundation — CURRENT

- [x] Establish product position and principles.
- [x] Define adaptive UX direction.
- [x] Establish physical-vs-touch interaction principle.
- [x] Establish dark-room requirement.
- [x] Establish open NFC and hardware philosophy.
- [x] Establish Kids + Easy shared-platform direction.
- [ ] Complete core user journeys.
- [ ] Identify product risks and open questions.

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

- [ ] Audio engine comparison.
- [ ] UI stack comparison on Raspberry Pi 4 reference prototype.
- [ ] Display sleep/wake + dark-room spike.
- [ ] Rotary encoder/buttons spike.
- [ ] NFC spike.
- [ ] Podcast/RSS + local file content spike.
- [ ] Power-bank compatibility constraints.
- [ ] Alternative SBC evaluation.
- [ ] Licensing/commercial-distribution review of candidate dependencies.

## P3 — MVP definition

Freeze only after P1/P2 evidence.

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
- local Guardian setup/configuration.

## P4 — Alpha implementation

- [ ] Hardware abstraction.
- [ ] Content domain and storage.
- [ ] Playback application layer.
- [ ] Adaptive UI primitives.
- [ ] Guardian local management.
- [ ] NFC Actions.
- [ ] Scenes.
- [ ] Packaging/install/update path.

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
