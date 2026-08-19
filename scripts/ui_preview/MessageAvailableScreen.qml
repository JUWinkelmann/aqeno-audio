import QtQuick

// A personal message is available. Not a notification: no badge, no red
// counter, no banner, no blinking, no prompt to listen now (ADR 0027 § 9).
//
// New does not mean urgent. Available does not mean interrupt. It is reached
// like any other content — focus with SELECT, press to play — and never plays
// by itself.
//
// The heart carries "a personal message". **Who it is from is the weaker half**
// for anyone who cannot read a name, so where portrait material exists the
// person becomes the dominant mark and the heart becomes a small qualifier.
Item {
    id: root
    property var theme

    property string senderPortrait: ""
    property string senderText: qsTr("Nachricht von Oma")
    property string whenText: qsTr("heute Mittag")

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceMd

        SenderMark {
            anchors.horizontalCenter: parent.horizontalCenter
            theme: root.theme
            portrait: root.senderPortrait
            width: Math.min(root.width * 0.34, root.height * 0.52)
            height: width
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsLabels
            text: root.senderText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.titleSize
            font.weight: Font.DemiBold
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            text: root.whenText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.captionSize
        }
    }
}
