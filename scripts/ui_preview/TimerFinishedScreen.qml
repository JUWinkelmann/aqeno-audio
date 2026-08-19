import QtQuick

// The timer has finished. An ATTENTION-class moment (ADR 0027 § 2): it may be
// heard at night under a night-safe level, and it says one thing.
//
// **The state must not live in the word.** A running timer is a ring with an
// empty middle; a finished one is a solid disc. The silhouette changes, so the
// state is legible without reading and from across a room. The label below
// confirms it and never creates it — no standard checkmark is borrowed, because
// an unfamiliar symbol is only an unfamiliar symbol.
//
// No control label: how the state is ended is C2 in INTERACTION_MATRIX.md § 9
// and stays open.
Item {
    id: root
    property var theme

    property string label: qsTr("Fertig")
    property string contextText: qsTr("Zähneputzen")

    readonly property real ringSize: Math.min(width * 0.5, height * 0.66)

    Item {
        id: mark
        width: root.ringSize
        height: root.ringSize
        x: (root.width - root.ringSize) / 2
        y: (root.height - root.ringSize) / 2 - theme.spaceMd

        // The spent track stays, so the object is recognisably the same timer.
        TimerRing {
            anchors.fill: parent
            theme: root.theme
            remaining: 0
        }

        // What was an empty middle is now filled: the time has arrived.
        Rectangle {
            anchors.centerIn: parent
            width: parent.width * 0.62
            height: width
            radius: width / 2
            color: theme.accent
        }
    }

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: mark.bottom
        anchors.topMargin: theme.spaceMd
        spacing: theme.spaceXs

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsLabels
            text: root.label
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.titleSize
            font.weight: Font.DemiBold
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            text: root.contextText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
        }
    }
}
