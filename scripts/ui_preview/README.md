# Device UI design targets — not product surfaces

These QML files are **visual target states for capabilities AQENO does not have yet**: the clock,
the visual timer, the alarm and personal messages. They exist so the design can be looked at and
argued about before the capabilities are built.

They are deliberately outside `src/` and are **not reachable from the running Device UI**. An
unavailable capability has no device surface at all — `PRODUCT_FOUNDATION.md` P15 — so routing any
of these into `Main.qml` before its domain exists would be a product defect, not progress.

They carry no application state. Values are literal properties, chosen to show a representative
moment. Nothing here reads the library, the playback session or a clock.

Render them with:

    python scripts/device_ui_preview.py --out build/ui-preview

Each state is rendered at 800 × 480 and 480 × 320. Several are also rendered at presentation level
`visual` — the honest pre-reader test, showing what survives when no text is drawn at all — and the
message states additionally with placeholder sender material, to show the hierarchy a portrait would
create. None of that implies the domain or transport must carry portraits.

Two of them are moments rather than states. `MessageAvailableScreen` and `TimerFinishedScreen` are
driven entirely by one `phase` property from 0 to 1, which is why `device_ui_preview.py` can hold
them at five fixed points and render the sequence as stills. The same property makes the real
animation interruptible: there is no timeline to unwind, only a number to re-target.

They share `Theme.qml` and the shared visual primitives with the real surfaces, so a design decision
made here is the same decision the product will inherit. What they must not do is decide behaviour: the open interaction questions
in `docs/implementation/INTERACTION_MATRIX.md` § 9 — C1 snooze semantics and C2 cancelling a running
timer blind — stay open, and no screen here shows a control label that would quietly settle them.
