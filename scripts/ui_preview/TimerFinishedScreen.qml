import QtQuick

// The timer has finished. An ATTENTION-class moment (ADR 0027 § 2): it may be
// heard at night under a night-safe level, and it says one thing.
//
// The empty ring is the point — the area a person watched shrinking has reached
// zero, so the state is legible without reading. No control label: how the
// state is ended is C2 and stays open.
Item {
    id: root
    property var theme

    property string label: qsTr("Fertig")
    property string contextText: qsTr("Zähneputzen")

    readonly property real ringSize: Math.min(width * 0.5, height * 0.66)

    TimerRing {
        id: ring
        theme: root.theme
        remaining: 0
        width: root.ringSize
        height: root.ringSize
        x: (root.width - root.ringSize) / 2
        y: (root.height - root.ringSize) / 2 - theme.spaceMd

        Text {
            anchors.centerIn: parent
            text: root.label
            color: theme.accent
            font.family: theme.fontFamily
            font.pixelSize: Math.round(theme.titleSize * 1.1)
            font.weight: Font.DemiBold
        }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: ring.bottom
        anchors.topMargin: theme.spaceMd
        visible: !theme.compact
        text: root.contextText
        color: theme.inkMuted
        font.family: theme.fontFamily
        font.pixelSize: theme.bodySize
    }
}
