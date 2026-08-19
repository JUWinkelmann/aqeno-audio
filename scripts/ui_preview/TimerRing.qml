import QtQuick

// AQENO's visual timer: a ring whose coloured share shrinks as time runs out.
// ADR 0025 § 3 asks for remaining time as an *area*, so that someone who cannot
// read a clock still understands it. The shape is AQENO's own; no protected
// product design is reproduced.
Item {
    id: ring

    property var theme
    property real remaining: 1.0   // 1 = full, 0 = finished
    property color trackColor: theme ? theme.surface : "#12171d"
    property color fillColor: theme ? theme.accent : "#8ed7c2"

    onRemainingChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        antialiasing: true

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var cx = width / 2
            var cy = height / 2
            var thickness = Math.max(10, Math.min(width, height) * 0.16)
            var radius = Math.min(width, height) / 2 - thickness / 2

            ctx.lineWidth = thickness
            ctx.lineCap = "butt"

            ctx.beginPath()
            ctx.strokeStyle = ring.trackColor
            ctx.arc(cx, cy, radius, 0, Math.PI * 2)
            ctx.stroke()

            if (ring.remaining <= 0)
                return

            // Clockwise from twelve o'clock, so the coloured area empties the
            // way a person expects a countdown to empty.
            var start = -Math.PI / 2
            ctx.beginPath()
            ctx.strokeStyle = ring.fillColor
            ctx.arc(cx, cy, radius, start, start + Math.PI * 2 * ring.remaining)
            ctx.stroke()
        }
    }
}
