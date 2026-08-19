import QtQuick
import "../../src/aqeno/ui/qml"

// Who a personal message is from, before anyone can read a name.
//
// With a portrait, the person is the mark and a small heart says what kind of
// thing this is. Without one, the heart carries the whole meaning and the name
// is text. That fallback is honest rather than accessible: a pre-reader who has
// no portrait learns only "a personal message", not from whom.
//
// This implies **no** obligation on the domain or on transport to carry
// portraits. It records what the presentation could use if such material ever
// exists (brief § 8).
Item {
    id: root

    property var theme
    property string portrait: ""
    property real glow: 0.0
    readonly property bool hasPortrait: portrait !== ""

    // The frame every image on the device wears, at the same proportional
    // radius. A circular avatar crop would be a shape borrowed from messengers,
    // and a person is not a different kind of picture from a cover.
    ArtworkFrame {
        id: face
        anchors.fill: parent
        visible: root.hasPortrait
        theme: root.theme
        source: root.portrait

        // Nested inside the frame on purpose: the bands then paint over the
        // corner covers, so the rounded corners are lit rather than black.
        ArtworkGlow {
            anchors.fill: parent
            theme: root.theme
            cornerRadius: parent.cornerRadius
            tint: root.theme ? root.theme.accent : "#23d5b6"
            intensity: root.glow
        }
    }

    AqenoGlyph {
        id: heart
        theme: root.theme
        name: "heart"
        color: root.theme ? root.theme.accent : "#23d5b6"
        width: root.hasPortrait ? root.width * 0.26 : root.width * 0.72
        height: width
        anchors.centerIn: root.hasPortrait ? undefined : parent

        // A quiet ground so the mark stays legible over any portrait.
        Rectangle {
            anchors.centerIn: parent
            z: -1
            width: parent.width * 1.6
            height: width
            radius: width / 2
            visible: root.hasPortrait
            color: root.theme ? root.theme.background : "#000000"
        }
    }

    states: State {
        when: root.hasPortrait
        AnchorChanges {
            target: heart
            anchors.right: face.right
            anchors.bottom: face.bottom
        }
        PropertyChanges {
            target: heart
            // Inside the frame, not straddling it. Hung over the corner the
            // chip's dark ground cuts a bite out of whatever surrounds the
            // portrait — including the arrival ring.
            anchors.rightMargin: root.width * 0.05
            anchors.bottomMargin: root.width * 0.05
        }
    }
}
