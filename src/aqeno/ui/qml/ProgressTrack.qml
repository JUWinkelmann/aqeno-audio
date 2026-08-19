import QtQuick

// One progress language for every screen that has one (brief § 16): a dark
// inactive track, a bright restrained active run, rounded geometry, and a
// slightly brighter head so the leading edge reads as light rather than paint.
//
// Playback, messages and volume all use this. A screen does not invent its own.
Item {
    id: root

    property var theme
    property real fraction: 0.0
    property bool live: true
    property color activeColor: theme
        ? (live ? theme.accent : theme.inkMuted)
        : "#23d5b6"
    property int animationDuration: theme ? theme.durationBase : 220

    implicitHeight: theme ? theme.progressHeight : 8

    Rectangle {
        anchors.fill: parent
        radius: height / 2
        color: root.theme ? root.theme.track : "#232a32"
    }

    Item {
        anchors.fill: parent
        clip: true

        Rectangle {
            id: run
            width: Math.max(0, Math.min(1, root.fraction)) * parent.width
            height: parent.height
            radius: height / 2
            color: root.activeColor

            Behavior on width {
                NumberAnimation {
                    duration: root.animationDuration
                    easing.type: root.theme ? root.theme.easingStandard : Easing.OutCubic
                }
            }
            Behavior on color { ColorAnimation { duration: root.theme ? root.theme.durationBase : 220 } }

            // The head, not a highlight over the whole run: light gathers where
            // the progress currently is.
            Rectangle {
                anchors.right: parent.right
                height: parent.height
                width: Math.min(parent.width, parent.height * 2.4)
                radius: height / 2
                visible: root.fraction > 0.004
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.0) }
                    GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, root.live ? 0.30 : 0.12) }
                }
            }
        }
    }
}
