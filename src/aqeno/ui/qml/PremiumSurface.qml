import QtQuick

// Level 1 and 2 of AQENO's depth system (brief § 6, § 7).
//
// A surface is separated from the black environment by *light*, not by a
// border: a brighter top edge, a barely-there vertical gradient in the fill,
// and a faint bounce at the bottom. That is what a physical object does under
// room light, and it costs two rectangles — no shadow stack, no blur.
Item {
    id: root

    property var theme
    property real cornerRadius: theme ? theme.radius : 22
    property bool focused: false

    // The fill lifts slightly when focused, so depth reinforces focus without
    // needing colour (brief § 9).
    readonly property color baseColor: theme
        ? (focused ? theme.surfaceFocused : theme.surface)
        : "#0b0f14"
    readonly property real hair: theme ? Math.max(1, Math.round(theme.unit)) : 1

    // The edge itself. Brightest where light would fall, weakest in the middle,
    // with a slight return at the bottom so the object reads as rounded.
    Rectangle {
        anchors.fill: parent
        radius: root.cornerRadius
        gradient: Gradient {
            GradientStop {
                position: 0.0
                color: root.theme
                    ? (root.focused ? root.theme.edgeLight : root.theme.edgeLightSoft)
                    : "#1a1a1a"
            }
            GradientStop { position: 0.5; color: Qt.rgba(1, 1, 1, 0.015) }
            GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, root.focused ? 0.05 : 0.025) }
        }

        Behavior on opacity { NumberAnimation { duration: root.theme ? root.theme.durationBase : 220 } }
    }

    Rectangle {
        anchors.fill: parent
        anchors.margins: root.hair
        radius: Math.max(0, root.cornerRadius - root.hair)
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.lighter(root.baseColor, 1.5) }
            GradientStop { position: 0.62; color: root.baseColor }
            GradientStop { position: 1.0; color: Qt.darker(root.baseColor, 1.35) }
        }
    }
}
