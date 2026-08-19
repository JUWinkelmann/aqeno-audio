import QtQuick
import "../../src/aqeno/ui/qml"

// Setting a timer: SELECT rotates the value, its press confirms. The ring grows
// with the chosen duration, so the size of the coming wait is visible before it
// starts. No instruction text — a surface that needs explaining is the wrong
// surface (DEVICE_UI_PRINCIPLES.md rule 1).
Item {
    id: root
    property var theme

    property string valueText: "12:00"
    property real fraction: 0.4      // of the settable range

    readonly property real ringSize: Math.min(width * 0.46, height * 0.62)

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceMd

        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: root.ringSize
            height: root.ringSize

            AmbientGlow {
                anchors.centerIn: parent
                width: parent.width * 1.7
                height: parent.height * 1.7
                theme: root.theme
                tint: theme.accent
                intensity: 0.35
                core: 0.5
                peak: 0.16
            }

            ProgressRing {
                anchors.fill: parent
                theme: root.theme
                fraction: root.fraction
                thickness: Math.min(width, height) * 0.085
            }

            Text {
                anchors.centerIn: parent
                text: root.valueText
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: Math.round(theme.titleSize * 1.4)
                font.weight: Font.DemiBold
                font.features: theme.numericFeatures
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsLabels
            text: qsTr("Timer")
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
        }
    }
}
