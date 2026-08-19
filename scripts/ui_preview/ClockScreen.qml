import QtQuick

// Idle clock. A quiet radio-alarm face and nothing else: no weather, no feed,
// no calendar, no smart-home state, no notifications (brief § 16).
// It is an AMBIENT-class presentation and never an inactivity fallback (P14).
Item {
    id: root
    property var theme

    property string timeText: "21:42"
    property string dayText: "Dienstag"

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
            visible: !theme.compact
            text: root.dayText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
        }
    }
}
