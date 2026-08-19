import QtQuick

// Who a personal message is from, before anyone can read a name.
//
// With a portrait, the person is the mark and a small heart says what kind of
// thing this is. Without one, the heart carries the whole meaning and the name
// is text. That fallback is honest rather than accessible: a pre-reader who has
// no portrait learns only "a personal message", not from whom.
//
// This implies **no** obligation on the domain or on transport to carry
// portraits. It records what the presentation could use if such material ever
// exists (brief § 8).
Item {
    id: root

    property var theme
    property string portrait: ""
    readonly property bool hasPortrait: portrait !== ""

    // Square with the product's small radius, like every other image AQENO
    // shows. A circular crop would need masking, which this Qt build renders
    // as an empty square inside a delegate — and consistency with ArtworkFrame
    // is worth more than an avatar shape borrowed from messengers anyway.
    Rectangle {
        id: disc
        anchors.fill: parent
        visible: root.hasPortrait
        radius: theme ? theme.radiusSm : 12
        color: theme ? theme.surface : "#12171d"
        clip: true

        Image {
            anchors.fill: parent
            source: root.portrait
            fillMode: Image.PreserveAspectCrop
            asynchronous: false
        }
    }

    Canvas {
        id: heart
        antialiasing: true
        width: root.hasPortrait ? root.width * 0.36 : root.width
        height: width
        anchors.right: root.hasPortrait ? disc.right : undefined
        anchors.bottom: root.hasPortrait ? disc.bottom : undefined
        anchors.rightMargin: root.hasPortrait ? -width * 0.22 : 0
        anchors.bottomMargin: root.hasPortrait ? -height * 0.22 : 0
        anchors.centerIn: root.hasPortrait ? undefined : parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var w = width
            var h = height
            if (root.hasPortrait) {
                // A quiet ground so the mark stays legible over any portrait.
                ctx.fillStyle = theme.background
                ctx.beginPath()
                ctx.arc(w / 2, h / 2, w / 2, 0, Math.PI * 2)
                ctx.fill()
            }
            var s = root.hasPortrait ? 0.74 : 1.0
            var ox = w * (1 - s) / 2
            var oy = h * (1 - s) / 2
            var pw = w * s
            var ph = h * s
            ctx.fillStyle = theme.accent
            ctx.beginPath()
            ctx.moveTo(ox + pw * 0.5, oy + ph * 0.86)
            ctx.bezierCurveTo(ox + pw * 0.06, oy + ph * 0.56,
                              ox + pw * 0.12, oy + ph * 0.14,
                              ox + pw * 0.5, oy + ph * 0.32)
            ctx.bezierCurveTo(ox + pw * 0.88, oy + ph * 0.14,
                              ox + pw * 0.94, oy + ph * 0.56,
                              ox + pw * 0.5, oy + ph * 0.86)
            ctx.closePath()
            ctx.fill()
        }
    }
}
