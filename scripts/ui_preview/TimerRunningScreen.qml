import QtQuick
import "../../src/aqeno/ui/qml"

// A running timer. The shrinking area is the primary carrier of meaning and the
// numerals are secondary, because a three-year-old cannot read a clock but can
// see that less is left (ADR 0025 § 3).
//
// The ring is the product's `ProgressRing` — the same object playback progress
// uses. AQENO has one ring language, not a timer ring and a playback ring
// (brief § 57).
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

    readonly property real ringSize: Math.min(width * 0.46, height * 0.62)

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceMd

        Item {
            id: ring
            anchors.horizontalCenter: parent.horizontalCenter
            width: root.ringSize
            height: root.ringSize

            AmbientGlow {
                anchors.centerIn: parent
                width: parent.width * 1.7
                height: parent.height * 1.7
                theme: root.theme
                tint: theme.accent
                intensity: 0.5
                core: 0.5
                peak: 0.16
            }

            ProgressRing {
                anchors.fill: parent
                theme: root.theme
                fraction: root.remaining
                thickness: Math.min(width, height) * 0.085
            }

            Text {
                anchors.centerIn: parent
                text: root.remainingText
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: Math.round(theme.titleSize * 1.4)
                font.weight: Font.DemiBold
                // Tabular figures: a countdown must not twitch as digits change
                // width (brief § 26).
                font.features: theme.numericFeatures
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            text: root.humanText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
        }
    }
}
