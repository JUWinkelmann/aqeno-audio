import QtQuick 2.15

// The AQENO device design system. Small on purpose: enough that every surface
// visibly comes from one product, and no more (AGENTS.md, "no premature
// abstraction"). Every screen reads its geometry from `unit` so the same
// hierarchy survives from a ~4" panel to RH1's 7" one (ADR 0026, ADR 0025 § 1).
QtObject {
    id: theme

    // Set once by Main.qml from the window size.
    property real viewportWidth: 800
    property real viewportHeight: 480

    // Sub-linear so a small panel keeps *relatively* larger type and focus
    // areas rather than a shrunken copy of the 7" composition.
    readonly property real rawScale: Math.min(viewportWidth / 800, viewportHeight / 480)
    readonly property real unit: Math.max(0.62, Math.min(1.4, Math.pow(rawScale, 0.7)))

    // Below this, secondary context is dropped rather than crammed in.
    readonly property bool compact: Math.min(viewportWidth, viewportHeight) < 380
    readonly property bool wide: viewportWidth > viewportHeight * 1.45

    // --- presentation level ---------------------------------------------
    // `visual` · `visual_label` · `informative`. Density only: no level changes
    // navigation, available functions, control semantics or touch. It is not an
    // age classification (`DEVICE_UI_PRINCIPLES.md` § Presentation levels).
    property string presentationLevel: "visual_label"

    readonly property bool showsLabels: presentationLevel !== "visual"
    readonly property bool showsDetails: presentationLevel === "informative" && !compact
    // Two independent reasons to say less: who is looking, and how much room
    // there is. A small panel drops detail even at `informative`.

    // --- colour ---------------------------------------------------------
    // Accent is one voice, not a status palette: it marks *the live thing* —
    // what is playing, what remains, what has arrived. It never carries a
    // meaning alone; form, size and position do that first, and colour
    // confirms (ADR 0026 § 1, P22). AQENO needs no colour-coded status
    // language, so no second or third accent is introduced.
    // True black is deliberate: it is free contrast on an LCD and genuine
    // pixel-off on the preferred later AMOLED panel. Nothing important is
    // defined by black alone, so RH1's LCD loses nothing (ADR 0025 § 1).
    readonly property color background: "#000000"
    readonly property color surface: "#12171d"
    readonly property color surfaceRaised: "#1c232b"
    readonly property color hairline: "#2b343e"
    readonly property color ink: "#f6f8fb"
    readonly property color inkMuted: "#9aa5b3"
    readonly property color accent: "#8ed7c2"
    readonly property color attention: "#f1bd78"

    // --- type -----------------------------------------------------------
    readonly property int displaySize: Math.round(66 * unit)
    readonly property int titleSize: Math.round(40 * unit)
    readonly property int bodySize: Math.round(26 * unit)
    readonly property int captionSize: Math.round(20 * unit)
    readonly property string fontFamily: "Inter"

    // --- spacing --------------------------------------------------------
    readonly property int spaceXs: Math.round(6 * unit)
    readonly property int spaceSm: Math.round(12 * unit)
    readonly property int spaceMd: Math.round(24 * unit)
    readonly property int spaceLg: Math.round(40 * unit)
    readonly property int edge: Math.round(36 * unit)

    // --- shape ----------------------------------------------------------
    readonly property int radius: Math.round(22 * unit)
    readonly property int radiusSm: Math.round(12 * unit)
    readonly property int focusRingWidth: Math.round(6 * unit)
    readonly property int progressHeight: Math.round(8 * unit)

    // --- motion ---------------------------------------------------------
    // Motion explains a change of focus or surface. Nothing loops, nothing
    // bounces, nothing asks to be looked at (PRODUCT_FOUNDATION.md P19).
    readonly property int durationFast: 120
    readonly property int durationBase: 200

    // Presentation timing, not a product timeout: how long a transient
    // acknowledgement stays before the previous surface returns. Documented in
    // CONFIGURATION_DEFAULTS.md § 1 as a presentation constant.
    readonly property int overlayDwellMs: 1800

    // Home's areas are named here, in content language. The application layer
    // keeps stable keys so a translation never reaches into it.
    function sectionTitle(key) {
        switch (key) {
        case "audio_drama": return qsTr("Hörspiele")
        case "audiobook": return qsTr("Hörbücher")
        case "music": return qsTr("Musik")
        case "podcast": return qsTr("Podcasts")
        case "radio": return qsTr("Radio")
        case "personal": return qsTr("Persönliches")
        }
        return ""
    }

    // Human sentences, never a code or a technical cause (FAILURE_STATES.md).
    function failureText(code) {
        switch (code) {
        case "source_missing":
        case "source_unreadable":
            return qsTr("Das lässt sich gerade nicht abspielen.")
        case "stream_unreachable":
            return qsTr("Das Radio ist gerade nicht erreichbar.")
        case "stream_interrupted":
            return qsTr("Die Verbindung ist abgerissen.")
        case "codec_unsupported":
        case "decode_failed":
            return qsTr("Das lässt sich gerade nicht abspielen.")
        }
        return qsTr("Das hat nicht geklappt.")
    }
}
