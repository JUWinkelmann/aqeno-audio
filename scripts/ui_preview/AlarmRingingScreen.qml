import QtQuick

// A ringing alarm. The most reduced surface AQENO has: a large time, a human
// greeting, and what is sounding. No menu, no navigation, no touch dependency.
//
// **Deliberately no control labels.** Which control snoozes and which ends the
// alarm is C1 in INTERACTION_MATRIX.md § 9 and is genuinely open — the proposal
// puts snooze on the VOLUME press, which sits in tension with that control's
// permanent meaning. Printing either label here would settle by drawing what
// has not been decided, so the layout is built to accept a hint line later
// without moving anything above it.
Item {
    id: root
    property var theme

    // A frame nothing else in AQENO wears. Clock is a bare time, the timer is a
    // circle and a message is a heart, so this state is distinguishable at two
    // metres by silhouette rather than by colour or by reading. It is static:
    // audio carries the time-critical attention (ADR 0027 § 5), and a display
    // must not try to do that job with animation.
    Rectangle {
        anchors.fill: parent
        anchors.margins: theme.spaceSm
        radius: theme.radius
        color: "transparent"
        border.width: Math.round(10 * theme.unit)
        border.color: theme.accent
    }

    property string timeText: "07:00"
    property string greetingText: qsTr("Guten Morgen")
    property string sourceText: qsTr("Nordwelle")

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceSm

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.timeText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: Math.round(theme.displaySize * 2.1)
            font.weight: Font.Light
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsLabels
            text: root.greetingText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.titleSize
            font.weight: Font.DemiBold
        }

        Item { width: 1; height: theme.spaceSm }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            spacing: theme.spaceSm

            Rectangle {
                width: Math.round(10 * theme.unit)
                height: width
                radius: width / 2
                color: theme.accent
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: root.sourceText
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.bodySize
            }
        }
    }
}
