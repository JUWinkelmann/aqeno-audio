import QtQuick
import "../../src/aqeno/ui/qml"

// Idle clock. A quiet radio-alarm face and nothing else: no weather, no feed,
// no calendar, no smart-home state, no notifications (brief § 16).
// It is an AMBIENT-class presentation and never an inactivity fallback (P14).
Item {
    id: root
    property var theme

    property string timeText: "21:42"
    property string dayText: "Dienstag"

    // A trace of warmth at the bottom edge, as if from somewhere below the
    // device. It is one gradient, it never moves, and at `ambience: 0` the
    // panel is exactly black — which is what DARK has to mean, and what an
    // AMOLED panel needs to actually switch its pixels off (P24, ADR 0025 § 1).
    property real ambience: 0.5

    Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: parent.height * 0.42
        opacity: root.ambience
        gradient: Gradient {
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop {
                position: 1.0
                color: Qt.rgba(theme.attention.r, theme.attention.g, theme.attention.b, 0.16)
            }
        }
    }

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceSm

        AqenoGlyph {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.round(theme.bodySize * 1.5)
            height: width
            theme: root.theme
            name: "moon"
            color: theme.inkMuted
            opacity: 0.7
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.timeText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: Math.round(theme.displaySize * 2.1)
            font.weight: Font.Light
            font.features: theme.numericFeatures
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            text: root.dayText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
        }
    }
}
