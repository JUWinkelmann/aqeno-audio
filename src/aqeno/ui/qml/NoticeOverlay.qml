import QtQuick 2.15

// A calm, transient sentence. Used where an action produced no inherent
// feedback of its own — an unassigned token being the case that exists today
// (CONFIGURATION_DEFAULTS.md § 6). Never technical, never a dead end.
Item {
    id: root

    property var theme
    property string message: ""
    property bool showing: false

    opacity: showing ? 1.0 : 0.0
    visible: opacity > 0.01

    Behavior on opacity { NumberAnimation { duration: theme.durationBase } }

    function show(text) {
        root.message = text
        root.showing = true
        dwell.restart()
    }

    Timer {
        id: dwell
        interval: theme.overlayDwellMs
        onTriggered: root.showing = false
    }

    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.74, 560 * theme.unit)
        height: label.height + theme.spaceLg * 2
        radius: theme.radius
        color: theme.surfaceRaised
        border.width: 1
        border.color: theme.hairline

        Text {
            id: label
            anchors.centerIn: parent
            width: parent.width - theme.spaceLg * 2
            text: root.message
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }
    }
}
