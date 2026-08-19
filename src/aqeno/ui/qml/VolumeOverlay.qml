import QtQuick 2.15

// Transient volume feedback. It never *causes* a wake — the display machine
// keeps volume outside Group G on purpose — so this only becomes visible when
// the panel is already lit (ADR 0026 § 5, DISPLAY_STATE_MACHINE.md note 6).
Item {
    id: root

    property var theme
    property var ui

    property bool showing: false
    property int lastVolume: -1

    opacity: showing ? 1.0 : 0.0
    visible: opacity > 0.01

    Behavior on opacity { NumberAnimation { duration: theme.durationFast } }

    Connections {
        target: ui
        function onStateChanged() {
            if (root.lastVolume === ui.volume)
                return
            var first = root.lastVolume < 0
            root.lastVolume = ui.volume
            if (first)
                return
            root.showing = true
            dwell.restart()
        }
    }

    Timer {
        id: dwell
        interval: theme.overlayDwellMs
        onTriggered: root.showing = false
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.62, 460 * theme.unit)
        height: content.height + theme.spaceLg * 2
        radius: theme.radius
        color: theme.surfaceRaised
        border.width: 1
        border.color: theme.hairline

        Column {
            id: content
            anchors.centerIn: parent
            width: parent.width - theme.spaceLg * 2
            spacing: theme.spaceSm

            Text {
                text: qsTr("Lautstärke")
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.captionSize
            }

            Rectangle {
                width: parent.width
                height: theme.progressHeight * 1.5
                radius: height / 2
                color: theme.hairline

                Rectangle {
                    width: parent.width * Math.max(0, Math.min(1, ui.volume / 100))
                    height: parent.height
                    radius: parent.radius
                    color: theme.accent

                    Behavior on width { NumberAnimation { duration: theme.durationFast } }
                }
            }

            Text {
                text: ui.volume + " %"
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: theme.bodySize
                font.weight: Font.DemiBold
            }
        }
    }
}
