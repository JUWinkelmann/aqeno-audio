import QtQuick

// The context-action pattern: a visual action carousel, not a text menu.
//
// SELECT rotates between actions, its press executes the focused one, HOME
// still rescues, and a visible action may also be tapped — the same action,
// never a touch-only path. It is deliberately small: two to four actions, and a
// screen that seems to need more has an information-architecture problem rather
// than a need for a "More…" bin, which is semantically weak for a pre-reader.
//
// **The three objects here are placeholders and mean nothing.** AQENO has no
// set of decided device context actions — favourites exist in the domain
// (ADR 0019) but device-side favouriting was never decided, and the sleep timer
// exists only as settings. Drawing invented actions to make a nicer picture is
// exactly what this preview must not do, so this screen evaluates geometry,
// dominance, hint size and scale only. Symbol recognisability cannot be judged
// until the real actions exist.
Item {
    id: root
    property var theme

    property int focusIndex: 1
    property int actionCount: 3

    readonly property real cardSize: Math.min(width * 0.3, height * 0.46)
    readonly property real step: cardSize + theme.spaceLg

    Row {
        id: row
        spacing: theme.spaceLg
        height: root.cardSize
        y: (root.height - root.cardSize) / 2 - theme.spaceMd
        x: root.width / 2 - root.cardSize / 2 - root.focusIndex * root.step

        Repeater {
            model: root.actionCount

            delegate: Item {
                readonly property bool focused: index === root.focusIndex

                width: root.cardSize
                height: root.cardSize
                opacity: focused ? 1.0 : 0.3
                scale: focused ? 1.0 : 0.84

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: -theme.focusRingWidth * 1.5
                    radius: theme.radius + theme.focusRingWidth * 1.5
                    visible: parent.focused
                    color: "transparent"
                    border.width: theme.focusRingWidth
                    border.color: theme.ink
                }

                Rectangle {
                    anchors.fill: parent
                    radius: theme.radius
                    color: theme.surfaceRaised

                    // A neutral silhouette standing in for an action object.
                    // Large, low-detail, warm rather than technical — the shape
                    // language a real action would have to satisfy.
                    Rectangle {
                        anchors.centerIn: parent
                        width: parent.width * 0.42
                        height: width
                        radius: width * 0.3
                        color: theme.hairline
                    }
                }
            }
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: row.bottom
        anchors.topMargin: theme.spaceLg
        visible: theme.showsLabels
        text: qsTr("Aktion")
        color: theme.ink
        font.family: theme.fontFamily
        font.pixelSize: theme.titleSize
        font.weight: Font.DemiBold
    }
}
