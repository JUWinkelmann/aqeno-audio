import QtQuick
import QtQuick.Shapes

// Every AQENO symbol, in one place (brief § 34). No icon library is mixed in:
// the shapes are drawn here, share one weight and one softness, and are meant
// to be recognised at two metres rather than admired at arm's length.
//
// Isolating them means a symbol can be redrawn later without any screen
// changing shape around it. `DEVICE_UI_PRINCIPLES.md` still applies: an unknown
// symbol is only an unknown symbol, so a glyph confirms meaning that position,
// size and context already carry.
Item {
    id: root

    property var theme
    property string name: ""
    property color color: theme ? theme.ink : "#f4f7f9"

    // Drawn in a 100 × 100 space and scaled as a whole, so one path definition
    // serves every size.
    readonly property string _fill: {
        switch (name) {
        case "speaker":
            return "M8 40 H26 L46 21 C48 19 50 20 50 23 V77 C50 80 48 81 46 79 "
                 + "L26 60 H8 C6 60 5 59 5 57 V43 C5 41 6 40 8 40 Z"
        case "bell":
            return "M50 10 C36 10 25 21 25 36 V52 C25 58 22 63 17 67 "
                 + "C14 69 15 74 19 74 H81 C85 74 86 69 83 67 "
                 + "C78 63 75 58 75 52 V36 C75 21 64 10 50 10 Z "
                 + "M41 80 H59 C59 87 55 92 50 92 C45 92 41 87 41 80 Z"
        case "heart":
            return "M50 86 C6 56 12 14 50 32 C88 14 94 56 50 86 Z"
        case "moon":
            return "M14 50 a36 36 0 1 0 72 0 a36 36 0 1 0 -72 0 "
                 + "M34 44 a31 31 0 1 0 62 0 a31 31 0 1 0 -62 0"
        case "pause":
            return "M34 22 H44 A5 5 0 0 1 49 27 V73 A5 5 0 0 1 44 78 H34 "
                 + "A5 5 0 0 1 29 73 V27 A5 5 0 0 1 34 22 Z "
                 + "M56 22 H66 A5 5 0 0 1 71 27 V73 A5 5 0 0 1 66 78 H56 "
                 + "A5 5 0 0 1 51 73 V27 A5 5 0 0 1 56 22 Z"
        }
        return ""
    }

    readonly property string _stroke: {
        switch (name) {
        case "speaker":
            return "M62 34 C71 43 71 57 62 66 M76 22 C91 38 91 62 76 78"
        }
        return ""
    }

    readonly property bool _oddEven: name === "moon"
    readonly property real _strokeWeight: 8

    Shape {
        anchors.centerIn: parent
        width: 100
        height: 100
        antialiasing: true
        scale: Math.min(root.width, root.height) / 100

        ShapePath {
            fillColor: root._fill === "" ? "transparent" : root.color
            strokeColor: "transparent"
            fillRule: root._oddEven ? ShapePath.OddEvenFill : ShapePath.WindingFill
            PathSvg { path: root._fill }
        }

        ShapePath {
            fillColor: "transparent"
            strokeColor: root._stroke === "" ? "transparent" : root.color
            strokeWidth: root._strokeWeight
            capStyle: ShapePath.RoundCap
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: root._stroke }
        }
    }
}
