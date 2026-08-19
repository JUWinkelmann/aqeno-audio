import QtQuick
import "../../src/aqeno/ui/qml"

// The timer has finished. An ATTENTION-class moment (ADR 0027 § 2): it may be
// heard at night under a night-safe level, and it says one thing.
//
// **The state must not live in the word.** A running timer is a ring with an
// empty middle; a finished one is a solid disc. The silhouette changes, so the
// state is legible without reading and from across a room. The label below
// confirms it and never creates it — no standard checkmark is borrowed, because
// an unfamiliar symbol is only an unfamiliar symbol. The approved reference
// shows a tick here; the silhouette rule is the older and stronger commitment,
// so the disc stays and the arrival is carried by motion instead.
//
// No control label: how the state is ended is C2 in INTERACTION_MATRIX.md § 9
// and stays open.
Item {
    id: root
    property var theme

    property string label: qsTr("Fertig")
    property string contextText: qsTr("Zähneputzen")

    // 0 = the last moment of running, 1 = settled. Driven by `arrival` in normal
    // use and set directly when a still has to be reviewable (brief § 51).
    property real phase: 1

    readonly property real ringSize: Math.min(width * 0.46, height * 0.62)

    function replay() {
        phase = 0
        arrival.restart()
    }

    // Ring completes, the middle fills, a few points of light leave, everything
    // settles. Around a second, then still — a finished timer is not an
    // animation that keeps running (brief § 52, P19).
    NumberAnimation {
        id: arrival
        target: root
        property: "phase"
        from: 0
        to: 1
        duration: theme ? theme.durationCelebration : 1150
        easing.type: Easing.OutCubic
    }

    function _span(from, to) {
        return Math.max(0, Math.min(1, (root.phase - from) / (to - from)))
    }

    Column {
        anchors.centerIn: parent
        spacing: theme.spaceMd

        Item {
            anchors.horizontalCenter: parent.horizontalCenter
            width: root.ringSize
            height: root.ringSize

            // One soft pulse as the moment lands, then nothing.
            scale: 1 + 0.06 * Math.sin(Math.PI * root._span(0.25, 0.75))

            AmbientGlow {
                anchors.centerIn: parent
                width: parent.width * 2.0
                height: parent.height * 2.0
                theme: root.theme
                tint: theme.accent
                intensity: 0.35 + 0.65 * root._span(0.2, 0.6)
                core: 0.28
                peak: 0.22
            }

            ProgressRing {
                anchors.fill: parent
                theme: root.theme
                fraction: root._span(0.0, 0.45)
                thickness: Math.min(width, height) * 0.085
            }

            // What was an empty middle is now filled: the time has arrived.
            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 0.46
                height: width
                radius: width / 2
                color: theme.accent
                scale: root._span(0.35, 0.7)
            }

            CelebrationLights {
                anchors.centerIn: parent
                width: parent.width * 2.1
                height: parent.height * 2.1
                theme: root.theme
                tint: theme.accent
                phase: root._span(0.4, 1.0)
                from: 0.32
                to: 0.62
            }
        }

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: theme.spaceXs
            opacity: root._span(0.55, 0.9)

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: theme.showsLabels
                text: root.label
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: theme.titleSize
                font.weight: Font.DemiBold
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: theme.showsDetails
                text: root.contextText
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.bodySize
            }
        }
    }
}
