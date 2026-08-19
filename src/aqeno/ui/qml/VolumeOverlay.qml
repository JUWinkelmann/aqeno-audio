import QtQuick

// Transient volume feedback. It never *causes* a wake — the display machine
// keeps volume outside Group G on purpose — so this only becomes visible when
// the panel is already lit (ADR 0026 § 5, DISPLAY_STATE_MACHINE.md note 6).
//
// The value is a number and a bar, not a sentence: someone who cannot read
// "Lautstärke" can still see which way it went (brief § 32, § 55). VOLUME stays
// physical; nothing here is pressable.
Item {
    id: root

    property var theme
    property var ui

    property bool showing: false
    property int lastVolume: 0

    opacity: showing ? 1.0 : 0.0
    visible: opacity > 0.01

    Behavior on opacity { NumberAnimation { duration: theme.durationFast } }

    // Seeded with the volume the device already has, so the overlay reacts to a
    // *change* rather than to learning the current value — and so the very
    // first turn after a start still shows.
    Component.onCompleted: root.lastVolume = ui.volume

    Connections {
        target: ui
        function onStateChanged() {
            if (root.lastVolume === ui.volume)
                return
            root.lastVolume = ui.volume
            root.showing = true
            dwell.restart()
        }
    }

    Timer {
        id: dwell
        interval: theme.overlayDwellMs
        onTriggered: root.showing = false
    }

    // Depth level 3: the overlay comes forward and what it covers steps back.
    // A wash rather than a blur — the same separation for none of the cost.
    Rectangle {
        anchors.fill: parent
        color: theme.background
        opacity: 0.86
    }

    Item {
        id: panel
        anchors.centerIn: parent
        // Wide and low. A tall card here read as a dialog; volume is one value
        // moving along an axis, and the panel should have that shape.
        width: Math.min(parent.width * 0.46, 340 * theme.unit)
        height: content.height + theme.spaceLg * 2

        // Arrives and leaves with a small scale, so it reads as something
        // coming forward rather than a rectangle appearing (brief § 37).
        scale: root.showing ? 1.0 : 0.94
        Behavior on scale {
            NumberAnimation { duration: theme.durationFast; easing.type: theme.easingStandard }
        }

        PremiumSurface {
            anchors.fill: parent
            theme: root.theme
            focused: true
            cornerRadius: theme.radiusLg
        }

        Column {
            id: content
            anchors.centerIn: parent
            width: parent.width - theme.spaceLg * 2
            spacing: theme.spaceMd

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: theme.spaceMd

                AqenoGlyph {
                    anchors.verticalCenter: parent.verticalCenter
                    width: Math.round(theme.displaySize * 0.62)
                    height: width
                    theme: root.theme
                    name: "speaker"
                    color: theme.ink
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: ui.volume
                    color: theme.ink
                    font.family: theme.fontFamily
                    font.pixelSize: theme.displaySize
                    font.weight: Font.Medium
                    font.features: theme.numericFeatures
                }
            }

            ProgressTrack {
                width: parent.width
                theme: root.theme
                fraction: Math.max(0, Math.min(1, ui.volume / 100))
                animationDuration: theme.durationFast
            }
        }
    }
}
