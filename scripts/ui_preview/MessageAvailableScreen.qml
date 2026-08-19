import QtQuick

// A personal message is available. Not a notification: no badge, no red
// counter, no banner, no blinking, no prompt to listen now (ADR 0027 § 9).
//
// New does not mean urgent. Available does not mean interrupt. The screen says
// who it is from and lets the person decide, and it is reached like any other
// content — focus with SELECT, press to play. It never plays by itself.
Item {
    id: root
    property var theme

    property string senderText: qsTr("Nachricht von Oma")
    property string whenText: qsTr("heute Mittag")

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceMd

        // A heart, not an unread count: the presentation carries human meaning
        // rather than technical state (PRODUCT_FOUNDATION.md P16).
        Canvas {
            id: heart
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.round(theme.displaySize * 2.2)
            height: width
            antialiasing: true

            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var w = width
                var h = height
                ctx.fillStyle = theme.accent
                ctx.beginPath()
                ctx.moveTo(w * 0.5, h * 0.86)
                ctx.bezierCurveTo(w * 0.06, h * 0.56, w * 0.12, h * 0.14, w * 0.5, h * 0.32)
                ctx.bezierCurveTo(w * 0.88, h * 0.14, w * 0.94, h * 0.56, w * 0.5, h * 0.86)
                ctx.closePath()
                ctx.fill()
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.senderText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.titleSize
            font.weight: Font.DemiBold
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: !theme.compact
            text: root.whenText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.captionSize
        }
    }
}
