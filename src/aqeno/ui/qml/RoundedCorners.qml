import QtQuick
import QtQuick.Shapes

// The four slivers a rounded silhouette leaves inside its bounding box.
//
// AQENO needs them because `clip` on this Qt build is rectangular — a rounded
// Rectangle clips its children to the box, not to the shape — and a real mask
// renders as an empty black square inside a Repeater delegate. So the corners
// are painted rather than cut: whatever is behind the artwork paints them back
// to the surround, and whatever lights the artwork paints them back to light.
//
// One triangulated path, no shader, no render target. It is the same geometry
// in both cases, which is why it lives here once.
Shape {
    id: corners

    property real cornerRadius: 0
    property color color: "#000000"

    antialiasing: true

    ShapePath {
        fillColor: corners.color
        strokeColor: "transparent"
        fillRule: ShapePath.OddEvenFill
        PathSvg { path: corners._path }
    }

    readonly property string _path: {
        var w = Math.max(0, width)
        var h = Math.max(0, height)
        var r = Math.max(0, Math.min(cornerRadius, Math.min(w, h) / 2))
        if (w <= 0 || h <= 0 || r <= 0)
            return ""
        return "M0 0 H" + w + " V" + h + " H0 Z "
             + "M" + r + " 0 H" + (w - r)
             + " A" + r + " " + r + " 0 0 1 " + w + " " + r
             + " V" + (h - r)
             + " A" + r + " " + r + " 0 0 1 " + (w - r) + " " + h
             + " H" + r
             + " A" + r + " " + r + " 0 0 1 0 " + (h - r)
             + " V" + r
             + " A" + r + " " + r + " 0 0 1 " + r + " 0 Z"
    }
}
