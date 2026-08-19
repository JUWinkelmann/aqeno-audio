import QtQuick

// A running timer. The shrinking area is the primary carrier of meaning and the
// numerals are secondary, because a three-year-old cannot read a clock but can
// see that less is left (ADR 0025 § 3).
//
// Deliberately absent: any cancel affordance or control label. How a running
// timer is cancelled — and whether that is possible blind at all — is C2 in
// INTERACTION_MATRIX.md § 9 and is still open. A screen must not settle it.
Item {
    id: root
    property var theme

    property string remainingText: "12:00"
    property string humanText: qsTr("noch 12 Minuten")
    property real remaining: 0.62

    readonly property real ringSize: Math.min(width * 0.5, height * 0.66)

    TimerRing {
        id: ring
        theme: root.theme
        remaining: root.remaining
        width: root.ringSize
        height: root.ringSize
        x: (root.width - root.ringSize) / 2
        y: (root.height - root.ringSize) / 2 - theme.spaceMd

        Text {
            anchors.centerIn: parent
            text: root.remainingText
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
        visible: theme.showsDetails
        text: root.humanText
        color: theme.inkMuted
        font.family: theme.fontFamily
        font.pixelSize: theme.bodySize
    }
}
