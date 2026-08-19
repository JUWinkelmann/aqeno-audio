import QtQuick

// Setting a timer: SELECT rotates the value, its press confirms. The ring grows
// with the chosen duration, so the size of the coming wait is visible before it
// starts. No instruction text — a surface that needs explaining is the wrong
// surface (DEVICE_UI_PRINCIPLES.md rule 1).
Item {
    id: root
    property var theme

    property string valueText: "12:00"
    property real fraction: 0.4      // of the settable range

    readonly property real ringSize: Math.min(width * 0.5, height * 0.66)

    TimerRing {
        id: ring
        theme: root.theme
        remaining: root.fraction
        width: root.ringSize
        height: root.ringSize
        x: (root.width - root.ringSize) / 2
        y: (root.height - root.ringSize) / 2 - theme.spaceMd

        Text {
            anchors.centerIn: parent
            text: root.valueText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: Math.round(theme.titleSize * 1.4)
            font.weight: Font.DemiBold
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: ring.bottom
        anchors.topMargin: theme.spaceMd
        text: qsTr("Timer")
        color: theme.inkMuted
        font.family: theme.fontFamily
        font.pixelSize: theme.bodySize
    }
}
