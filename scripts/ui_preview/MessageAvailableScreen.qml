import QtQuick
import "../../src/aqeno/ui/qml"

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
//
// Arrival is a moment, not a state: light gathers, a ring closes, the person
// resolves, a few points of light leave, and then it is still. It runs once, in
// about a second, and never at night — arrival there is completely silent and
// unlit (ADR 0027 § 9). What remains afterwards is an ordinary calm surface.
Item {
    id: root
    property var theme

    property string senderPortrait: ""
    property string senderText: qsTr("Nachricht von Oma")
    property string whenText: qsTr("heute Mittag")

    // 0 = the instant before it exists, 1 = settled.
    property real phase: 1

    readonly property real markSize: Math.min(width * 0.30, height * 0.40)
    // The ring has to clear the mark it closes around. A portrait is a square,
    // so its diagonal sets the radius; a lone heart needs far less room, and a
    // ring sized for the square would leave it stranded in the middle.
    readonly property real ringSize:
        markSize * (senderPortrait !== "" ? 1.62 : 1.24)

    function replay() {
        phase = 0
        arrival.restart()
    }

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
            id: mark
            anchors.horizontalCenter: parent.horizontalCenter
            width: root.ringSize
            height: width

            // The ring closes around the person: the same motif the timer and
            // playback use, saying "this is about to be here". Once it has
            // closed it steps back — a ring left at full strength would be the
            // badge this screen is not allowed to have.
            ProgressRing {
                anchors.fill: parent
                theme: root.theme
                fraction: root._span(0.1, 0.6)
                thickness: Math.min(width, height) * 0.032
                bloom: 1.0 - root._span(0.6, 0.95)
                opacity: 1.0 - 0.62 * root._span(0.7, 1.0)
                trackColor: "transparent"
            }

            SenderMark {
                anchors.centerIn: parent
                theme: root.theme
                portrait: root.senderPortrait
                width: root.markSize
                height: width
                scale: 0.72 + 0.28 * root._span(0.3, 0.75)
                opacity: root._span(0.3, 0.7)
                // Light gathers, peaks as the ring closes, then falls back to a
                // low steady level: the surface has to look calm once the
                // moment has passed.
                glow: 1.4 * root._span(0.2, 0.5) - 0.9 * root._span(0.55, 0.9)
            }

            CelebrationLights {
                anchors.fill: parent
                theme: root.theme
                tint: theme.accent
                phase: root._span(0.45, 1.0)
                from: 0.55
                to: 0.98
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsLabels
            text: root.senderText
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.titleSize
            font.weight: Font.DemiBold
            opacity: root._span(0.6, 0.95)
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: theme.showsDetails
            text: root.whenText
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.captionSize
            opacity: root._span(0.7, 1.0)
        }
    }
}
