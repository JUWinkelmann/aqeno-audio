import QtQuick

// Light as a material (brief § 36) — done cheaply (brief, "visual fidelity
// through cheap primitives").
//
// A radial falloff painted **once per change** of tint or size and then held as
// a texture. Nothing here repaints per frame: brightness rides on the item's
// opacity, never on its paint. That is the difference between a halo AQENO can
// afford on a Pi 4 and a realtime blur it cannot.
Item {
    id: root

    property var theme
    property color tint: theme ? theme.accent : "#23d5b6"
    property real intensity: 1.0
    // How much of the radius is at full strength before the falloff starts.
    property real core: 0.16
    property real peak: 0.5

    // Intensity is the one property that gets animated, so it must not reach the
    // paint: it rides on the item's opacity and the texture stays valid.
    opacity: Math.max(0, Math.min(1, intensity))

    onTintChanged: canvas.requestPaint()
    onCoreChanged: canvas.requestPaint()
    onPeakChanged: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    Canvas {
        id: canvas
        anchors.fill: parent
        renderStrategy: Canvas.Cooperative

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (width <= 0 || height <= 0)
                return
            var cx = width / 2
            var cy = height / 2
            var radius = Math.min(width, height) / 2
            var gradient = ctx.createRadialGradient(
                cx, cy, radius * root.core, cx, cy, radius)
            var tint = root.tint
            gradient.addColorStop(0.0, Qt.rgba(tint.r, tint.g, tint.b, root.peak))
            gradient.addColorStop(0.42, Qt.rgba(tint.r, tint.g, tint.b, root.peak * 0.34))
            gradient.addColorStop(0.72, Qt.rgba(tint.r, tint.g, tint.b, root.peak * 0.10))
            gradient.addColorStop(1.0, Qt.rgba(tint.r, tint.g, tint.b, 0.0))
            ctx.fillStyle = gradient
            ctx.fillRect(0, 0, width, height)
        }
    }
}
