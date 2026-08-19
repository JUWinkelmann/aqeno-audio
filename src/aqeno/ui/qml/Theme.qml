import QtQuick

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
    // language, so the only second voice is `attention`, reserved for a
    // time-critical state that must be told apart from every calm one.
    //
    // True black is the *environment*, not a background fill: it is free
    // contrast on an LCD and genuine pixel-off on the preferred later AMOLED
    // panel. Objects emerge from it by luminance rather than by sitting on a
    // grey plane (ADR 0025 § 1).
    readonly property color background: "#000000"

    // Depth is four levels and no framework (brief § 6). Level 0 is the black
    // environment; 1 a surface that is barely there; 2 the focused object;
    // 3 a transient overlay that must read instantly.
    readonly property color surface: "#080b0e"
    readonly property color surfaceFocused: "#0e141a"
    readonly property color surfaceRaised: "#1a2028"
    readonly property color track: "#232a32"
    readonly property color hairline: "#2b343e"

    readonly property color ink: "#f4f7f9"
    readonly property color inkMuted: "#8e9aa6"
    readonly property color accent: "#23d5b6"
    readonly property color accentSoft: "#a7e3d0"
    readonly property color attention: "#ff8e72"

    // Edge light rather than a border: a surface is separated from black by a
    // brighter top edge, the way a physical object catches room light.
    readonly property color edgeLight: Qt.rgba(1, 1, 1, 0.10)
    readonly property color edgeLightSoft: Qt.rgba(1, 1, 1, 0.045)

    // --- type -----------------------------------------------------------
    // Inter (SIL OFL 1.1) is the blueprint's recorded candidate and is kept
    // rather than swapped for a rounded face: high legibility, modern
    // proportions, complete German coverage and real tabular figures. Nothing
    // in this repository installs it, so which face RH1 actually resolves is a
    // hardware question, not a settled one.
    readonly property string fontFamily: "Inter"

    // Time and durations are visual objects, not enlarged body text: tabular
    // figures stop a countdown from twitching as digits change width.
    readonly property var numericFeatures: ({ "tnum": 1 })

    readonly property int displaySize: Math.round(66 * unit)
    readonly property int titleSize: Math.round(40 * unit)
    readonly property int bodySize: Math.round(26 * unit)
    readonly property int captionSize: Math.round(20 * unit)

    // --- spacing --------------------------------------------------------
    readonly property int spaceXs: Math.round(6 * unit)
    readonly property int spaceSm: Math.round(12 * unit)
    readonly property int spaceMd: Math.round(24 * unit)
    readonly property int spaceLg: Math.round(40 * unit)
    readonly property int edge: Math.round(36 * unit)

    // --- shape ----------------------------------------------------------
    readonly property int radiusSm: Math.round(12 * unit)
    readonly property int radius: Math.round(22 * unit)
    readonly property int radiusLg: Math.round(34 * unit)
    readonly property int progressHeight: Math.round(8 * unit)

    // Artwork keeps a constant *proportional* radius so a cover reads as the
    // same object at any size, instead of looking sharper as it grows.
    function artworkRadius(size) {
        return Math.round(size * 0.19)
    }

    // How much room a card must reserve below its artwork. Kept here because
    // the carousel needs it to size the card before the card exists.
    function cardLabelBand() {
        var band = Math.round(7 * unit) + spaceXs
        if (showsLabels)
            band += Math.round(titleSize * 1.25)
        if (showsDetails)
            band += Math.round(captionSize * 1.4)
        return band
    }

    // --- focus ----------------------------------------------------------
    // Focus is carried by size, luminance, depth and neighbour suppression
    // before colour touches it, so it survives without colour perception
    // (brief § 9, ADR 0026 § 1).
    readonly property real focusScale: 1.0
    readonly property real restScale: 0.82
    readonly property real restOpacity: 0.38
    readonly property int focusEdgeWidth: Math.max(2, Math.round(2.5 * unit))

    // --- motion ---------------------------------------------------------
    // A small vocabulary rather than an animation per screen (brief § 37).
    // Motion explains a change of focus or surface. Nothing loops, nothing
    // bounces, nothing asks to be looked at (PRODUCT_FOUNDATION.md P19).
    readonly property int durationInstant: 90
    readonly property int durationFast: 140
    readonly property int durationBase: 220
    readonly property int durationCelebration: 1150
    readonly property int durationPulse: 1700

    // Deceleration only: an encoder detent should feel like a mechanism
    // settling, never like something springing back (brief § 11).
    readonly property int easingStandard: Easing.OutCubic
    readonly property int easingEmphasis: Easing.OutQuint

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
