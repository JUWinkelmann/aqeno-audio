import QtQuick

// The light a cover throws (brief § 14).
//
// Concentric rounded outlines that hug the artwork's silhouette and fall away
// exponentially. Each band lies entirely *outside* the artwork, so nothing is
// drawn over the image and the corners — which a rounded frame leaves empty —
// are lit rather than left as black notches.
//
// This is the cheap half of the trade the brief asks for: no blurred copy of
// the artwork, no shader, no render target. A handful of rounded rectangles and
// one precomputed tint, and the eye reads a rim of coloured light.
Item {
    id: root

    property var theme
    property color tint: theme ? theme.accent : "#23d5b6"
    property real intensity: 1.0
    property real cornerRadius: 0
    // How far the outermost band reaches, as a share of the artwork's width.
    // Long and faint rather than short and bright: a short reach at high alpha
    // reads as a drawn outline, which is the one thing this must not look like.
    property real spread: 0.46
    property real peak: 0.11

    // Enough bands that the falloff reads as light rather than as a stack of
    // outlines. They are plain rectangles, so this stays cheaper than one blur.
    readonly property int bands: 16
    readonly property real _reach: Math.max(8, width * spread)
    readonly property real _band: _reach / bands

    // Brightness rides on opacity rather than on sixteen band colours, so
    // fading the light in or out costs one node property per frame instead of
    // sixteen re-evaluated bindings.
    opacity: Math.max(0, Math.min(1, intensity))
    visible: opacity > 0.01

    Behavior on opacity {
        NumberAnimation { duration: root.theme ? root.theme.durationBase : 220 }
    }

    Repeater {
        model: root.bands

        delegate: Rectangle {
            readonly property real outer: (index + 1) * root._band

            anchors.centerIn: parent
            width: root.width + outer * 2
            height: root.height + outer * 2
            radius: root.cornerRadius + outer
            color: "transparent"
            // Bands overlap. Butted against each other they leave antialiased
            // hairlines that read as concentric outlines — the exact artefact
            // this is trying to avoid.
            border.width: root._band * 2.0
            border.color: Qt.rgba(
                root.tint.r, root.tint.g, root.tint.b,
                root.peak * Math.exp(-3.0 * (index / root.bands)))
        }
    }
}
