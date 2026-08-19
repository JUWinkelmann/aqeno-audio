import QtQuick

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

    // Depth level 3: the overlay comes forward and what it covers steps back.
    Rectangle {
        anchors.fill: parent
        color: theme.background
        opacity: 0.86
    }

    Item {
        id: panel
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.74, 560 * theme.unit)
        height: label.height + theme.spaceLg * 2

        scale: root.showing ? 1.0 : 0.96
        Behavior on scale {
            NumberAnimation { duration: theme.durationBase; easing.type: theme.easingStandard }
        }

        PremiumSurface {
            anchors.fill: parent
            theme: root.theme
            focused: true
            cornerRadius: theme.radiusLg
        }

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
