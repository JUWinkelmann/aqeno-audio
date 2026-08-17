# ADR 0002 — UI stack

**Status:** Accepted
**Date:** 2026-08-17
**Accepted:** 2026-08-17

## Context

AQENO needs a touch UI on a 7-inch Raspberry Pi display for Kids Early, Easy and Standard
experiences that share one adaptive core (`PRODUCT_FOUNDATION.md` § 4). The unusual requirement is
not the UI itself — it is that **the application must own the display's power state**.

`docs/product/DISPLAY_BEHAVIOR.md` requires an application-level state machine over
`OFF / DIM / INTERACTIVE / AMBIENT / SETUP`, explicitly *not* delegated to desktop-environment or
screensaver defaults, with true `OFF` while audio continues. `AGENTS.md` additionally forbids waking
the display for routine playback events. Any UI technology that does not let the application hold
the display dark while remaining live is disqualified regardless of its other merits.

Language is Python per ADR 0001. Licensing constraints are set by ADR 0004 and are load-bearing
here.

## Decision

**Qt 6 via PySide6, with Qt Quick / QML for the view layer.**

- **PySide6, not PyQt6.** PySide6 is LGPLv3; PyQt6 is GPLv3-or-commercial and would force the
  entire application to GPLv3 or require a paid Riverbank licence. See ADR 0004.
- **QML for views**, Python for view models. Touch handling, large forgiving targets, scaling and
  calm transitions are straightforward in QML, and the declarative split maps cleanly onto
  `PRODUCT_FOUNDATION.md`'s capability-driven variation: one component set, profile-driven
  configuration, not a Kids app and an Easy app.
- **Qt Virtual Keyboard is excluded.** ADR 0012 keeps complex text entry and administration off the
  appliance UI; no replacement keyboard is built without a concrete local-entry requirement. This
  also avoids the module's GPLv3/commercial licensing constraint.
- **Qt Multimedia is not used for playback.** Audio goes through the engine in ADR 0003, behind the
  audio port.
- **The Device UI runs in-process with the application core.** Concrete Python view models expose
  application state and intentions to QML through Qt properties/signals, not IPC. ADR 0012 separates
  this from a possible future Management API.

## Alternatives considered

**Python core plus web UI in a kiosk browser (Chromium/WPE).** Fastest UI iteration, largest pool
of contributors, and the best fit for delegating UI work to weaker models — a real cost of
rejecting it. Rejected on the two hard constraints: a browser adds substantial cold-boot cost
against a ≤ 10 s budget on a Pi 4, and it interposes itself between the application and the display,
making authoritative `OFF` and wake-without-flash awkward rather than designed. Display authority
is the product's core requirement, not a detail to work around.

**Qt Widgets instead of QML.** Lighter and faster to start, and a legitimate fallback if QML's
startup cost proves too high. Rejected as the default because the adaptive, image-first, large-touch
UI across three experience profiles is exactly what QML is good at, and Widgets would push that
variation into imperative Python.

**GTK4 via PyGObject.** Credible, LGPL, and already a dependency through GStreamer's Python
bindings. Rejected because Qt Quick's touch and scene-graph story on embedded Linux is stronger for
this use case and QML's declarative profile-driven variation is a better fit for the capability
model.

**Raw framebuffer / LVGL / custom renderer.** Best startup and total display control. Rejected as
disproportionate: it would consume the discovery phase building a UI toolkit instead of validating
the product.

## Consequences

**Easier.** Display state becomes ownable: Qt can run without a desktop environment (`eglfs`), so
the application controls the surface and can coordinate panel power with backlight control in the
display adapter. Adaptive UI variation is configuration over one component set. The in-process
decision collapses gap G07 for the Device UI — no local API, serialisation or authentication surface
is introduced by the first vertical slice.

**Harder.** Qt plus QML import and scene-graph warm-up is the largest single item in the cold-boot
budget, which reinforces the staged-readiness requirement from ADR 0001: input and audio adapters
must come up before the UI, and the UI must not gate them. Touch-wake from `OFF` must be verified to
produce no visible flash or partially-painted frame.

**Constrained.** LGPLv3 compliance is now a build and packaging requirement, not an afterthought:
Qt must be dynamically linked and replaceable on the shipped device. Details and obligations in
ADR 0004. The module restriction above must be checked whenever a new Qt module is introduced.

**Deferred.** Whether Qt is taken from Raspberry Pi OS packages or built/pinned separately, and
whether the app runs under `eglfs` or a Wayland compositor, are packaging decisions for a later
ADR — but they are the decisions that determine whether the display-power story actually works, so
they must be spiked before enclosure freeze.

**Open verification (P2 feasibility spike).** On Reference hardware: QML cold start to first frame;
true panel `OFF` with audio continuing; touch-wake latency against the ≤ 1 s target; no wake on
metadata or chapter change. If QML start cost breaks the budget irrecoverably, fall back to Qt
Widgets before abandoning Qt.
