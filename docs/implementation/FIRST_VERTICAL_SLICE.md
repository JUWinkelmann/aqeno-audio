# First Vertical Slice

## Objective
Prove the end-to-end AQENO architecture with the smallest useful experience.

## User-visible behaviour
1. AQENO starts on Linux.
2. Kids Early Home shows three mock/local items as large image tiles.
3. Selecting an item plays a local audio file.
4. Playback position is persisted and resumes.
5. Keyboard/simulator events emulate Volume, Play/Pause, Next and Previous.
6. A simulated NFC UID can launch one item.
7. After an inactivity timeout, display state becomes OFF while audio continues.
8. Physical/simulated Play/Pause and Volume work while OFF without changing display state.
9. Explicit WakeRequest returns to INTERACTIVE.
10. Network absence does not prevent local use.

## Implementation order
1. domain model + state machines;
2. persistence;
3. audio adapter behind interface;
4. semantic input bus + simulator;
5. application services;
6. local API/event channel;
7. Kids Early UI;
8. display policy;
9. end-to-end tests;
10. Reference Hardware adapter.

## Definition of done
- unit/state-machine tests green;
- restart preserves resume position;
- offline smoke test passes;
- dark-room test passes;
- no Pi-specific imports in domain/application layers;
- structured logs contain enough detail to diagnose failures;
- architecture changes recorded as ADRs.
