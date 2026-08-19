import QtQuick
import "../../src/aqeno/ui/qml"

// Playing a personal message. It is *content*, not a notification, so it looks
// like content and pauses media the way content does (ADR 0027 § 5) — the same
// hierarchy as Now Playing, with the person in place of artwork, and the same
// progress track. A message deserves no separate visual language.
//
// A delivered message is local and may be played again later (§ 8), so nothing
// here treats it as consumed or disappearing.
Item {
    id: root
    property var theme

    property string senderText: qsTr("Oma")
    property string whenText: qsTr("heute Mittag")
    property real progress: 0.42

    readonly property real markSize: Math.min(width * 0.28, height * 0.44)

    property string senderPortrait: ""

    Column {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.66, 620 * theme.unit)
        spacing: theme.spaceMd

        SenderMark {
            anchors.horizontalCenter: parent.horizontalCenter
            theme: root.theme
            portrait: root.senderPortrait
            width: root.markSize
            height: width
            // The same light a cover throws on Now Playing. A message is
            // content and gets the treatment content gets.
            glow: 0.7
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

        ProgressTrack {
            width: parent.width
            theme: root.theme
            fraction: root.progress
        }
    }
}
