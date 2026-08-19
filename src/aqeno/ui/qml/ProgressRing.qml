import QtQuick
import QtQuick.Shapes

// The ring: AQENO's recurring motif (brief § 57). It is the same object as the
// illuminated encoder the box will carry, which is why progress, a timer, a
// completion and an arriving message all speak through it — and why it is not
// put around things that are not one of those.
//
// Built from two stroked arcs plus a wider, dimmer arc behind the live one.
// That third stroke is the whole "luminous" effect: no blur, no shader, and a
// sweep animation only re-tessellates a handful of vertices.
Item {
    id: root

    property var theme
    property real fraction: 1.0
    property color trackColor: theme ? theme.track : "#232a32"
    property color arcColor: theme ? theme.accent : "#23d5b6"
    property real thickness: Math.max(4, Math.min(width, height) * 0.075)
    // Twelve o'clock, clockwise: the direction a person expects time to move.
    property real startAngle: -90
    property real bloom: 1.0

    readonly property real _radius: (Math.min(width, height) - thickness) / 2
    readonly property real _sweep: Math.max(0, Math.min(1, fraction)) * 360

    Shape {
        anchors.fill: parent
        antialiasing: true
        layer.enabled: false

        ShapePath {
            strokeColor: root.trackColor
            strokeWidth: root.thickness
            fillColor: "transparent"
            capStyle: ShapePath.FlatCap

            PathAngleArc {
                centerX: root.width / 2
                centerY: root.height / 2
                radiusX: root._radius
                radiusY: root._radius
                startAngle: 0
                sweepAngle: 360
            }
        }

        // The bloom: same arc, wider and faint. Reads as light spilling off the
        // stroke at a fraction of the cost of blurring it.
        ShapePath {
            strokeColor: Qt.rgba(root.arcColor.r, root.arcColor.g, root.arcColor.b,
                                 0.22 * root.bloom)
            strokeWidth: root.thickness * 2.1
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap

            PathAngleArc {
                centerX: root.width / 2
                centerY: root.height / 2
                radiusX: root._radius
                radiusY: root._radius
                startAngle: root.startAngle
                sweepAngle: root._sweep
            }
        }

        ShapePath {
            strokeColor: root.fraction > 0.001 ? root.arcColor : "transparent"
            strokeWidth: root.thickness
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap

            PathAngleArc {
                centerX: root.width / 2
                centerY: root.height / 2
                radiusX: root._radius
                radiusY: root._radius
                startAngle: root.startAngle
                sweepAngle: root._sweep
            }
        }
    }
}
