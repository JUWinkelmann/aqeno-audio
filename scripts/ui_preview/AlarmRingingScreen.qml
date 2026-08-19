import QtQuick
import "../../src/aqeno/ui/qml"

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

    property string timeText: "07:00"
    property string greetingText: qsTr("Guten Morgen")
    property string sourceText: qsTr("Nordwelle")

    // Concentric rings and a bell: a silhouette nothing else in AQENO wears.
    // Clock is a bare time, a timer is one ring, a message is a person, so this
    // state is told apart at two metres by shape rather than by colour or by
    // reading. It is static — audio carries the time-critical attention
    // (ADR 0027 § 5) and a display must not try to do that job with animation.
    //
    // Warm orange is the second voice, reserved for exactly this class of
    // moment; it confirms the silhouette and never carries it alone.
    Column {
        anchors.centerIn: parent
        spacing: theme.spaceMd

    Item {
        id: rings
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(root.width * 0.30, root.height * 0.42)
        height: width

        AmbientGlow {
            anchors.centerIn: parent
            width: parent.width * 1.9
            height: parent.height * 1.9
            theme: root.theme
            tint: theme.attention
            intensity: 0.6
            core: 0.3
            peak: 0.2
        }

        Repeater {
            model: 3

            delegate: Rectangle {
                readonly property real span: 1 - index * 0.24

                anchors.centerIn: parent
                width: parent.width * span
                height: width
                radius: width / 2
                color: "transparent"
                border.width: Math.max(2, parent.width * 0.028)
                border.color: Qt.rgba(root.theme.attention.r, root.theme.attention.g,
                                      root.theme.attention.b, 1 - index * 0.28)
            }
        }

        AqenoGlyph {
            anchors.centerIn: parent
            width: parent.width * 0.34
            height: width
            theme: root.theme
            name: "bell"
            color: theme.attention
        }
    }

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: theme.spaceXs

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.timeText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: Math.round(theme.displaySize * 1.2)
            font.weight: Font.Light
            font.features: theme.numericFeatures
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

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            spacing: theme.spaceSm
            topPadding: theme.spaceXs

            Rectangle {
                width: Math.round(10 * theme.unit)
                height: width
                radius: width / 2
                color: theme.attention
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
}
