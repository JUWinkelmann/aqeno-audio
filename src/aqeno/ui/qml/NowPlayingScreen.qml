import QtQuick 2.15

// Artwork, title, context, progress — and nothing else. The five physical
// controls already carry Previous, Next, Volume, Play/Pause and Home, so no
// virtual transport row exists (brief § 10, PRODUCT_FOUNDATION.md P20).
//
// Geometry is computed rather than anchored: the two arrangements differ too
// much for conditional anchors to stay readable or correct.
Item {
    id: root

    property var theme
    property var ui

    readonly property bool stacked: !theme.wide
    readonly property real pad: theme.edge
    readonly property real artSize: stacked
        ? Math.min(width * 0.46, height * 0.4)
        : Math.min(width * 0.34, height * 0.66)

    ArtworkFrame {
        id: art
        theme: root.theme
        source: ui.nowPlayingArtworkUrl
        width: root.artSize
        height: root.artSize
        x: root.stacked ? (root.width - root.artSize) / 2 : root.pad * 1.3
        y: root.stacked ? root.pad : (root.height - root.artSize) / 2
    }

    Column {
        id: details
        x: root.stacked ? root.pad : art.x + root.artSize + theme.spaceLg
        width: root.stacked
               ? root.width - root.pad * 2
               : root.width - (art.x + root.artSize + theme.spaceLg) - root.pad
        y: root.stacked
           ? art.y + root.artSize + theme.spaceMd
           : (root.height - height) / 2
        spacing: theme.spaceSm

        Text {
            width: parent.width
            visible: theme.showsLabels
            text: ui.nowPlayingTitle
            color: theme.ink
            font.family: theme.fontFamily
            font.pixelSize: theme.titleSize
            font.weight: Font.DemiBold
            horizontalAlignment: root.stacked ? Text.AlignHCenter : Text.AlignLeft
            wrapMode: Text.Wrap
            maximumLineCount: 2
            elide: Text.ElideRight
        }

        Text {
            width: parent.width
            visible: ui.nowPlayingChapter !== "" && theme.showsDetails
            text: ui.nowPlayingChapter
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
            horizontalAlignment: root.stacked ? Text.AlignHCenter : Text.AlignLeft
            elide: Text.ElideRight
        }

        // A failure is a state of this surface, never a modal dead end, and it
        // is phrased for the person rather than the log (FAILURE_STATES.md).
        Text {
            width: parent.width
            visible: ui.hasPlaybackFailure
            text: theme.failureText(ui.failureCode)
            color: theme.attention
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
            horizontalAlignment: root.stacked ? Text.AlignHCenter : Text.AlignLeft
            wrapMode: Text.Wrap
        }

        Item { width: 1; height: theme.spaceMd }

        Rectangle {
            width: parent.width
            height: theme.progressHeight
            radius: height / 2
            visible: !ui.hasPlaybackFailure
            color: theme.hairline

            Rectangle {
                width: parent.width * ui.progress
                height: parent.height
                radius: parent.radius
                color: ui.playing ? theme.accent : theme.inkMuted

                Behavior on width {
                    NumberAnimation { duration: theme.durationBase; easing.type: Easing.OutCubic }
                }
            }
        }

        Item {
            width: parent.width
            height: theme.captionSize + theme.spaceXs
            visible: !ui.hasPlaybackFailure && ui.durationText !== "" && theme.showsDetails

            Text {
                anchors.left: parent.left
                text: ui.positionText
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.captionSize
            }
            Text {
                anchors.right: parent.right
                text: ui.durationText
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.captionSize
            }
        }
    }

    // Paused reads from the artwork itself: the cover recedes and one large
    // mark sits over it. Not a control — nothing here is pressable, and the
    // physical VOLUME press remains the only way to resume. A corner chip was
    // too quiet to notice from across a room, which matters most for a person
    // who cannot simply hear that the audio stopped (brief § 29).
    Rectangle {
        anchors.fill: art
        radius: art.cornerRadius
        visible: !ui.playing && !ui.hasPlaybackFailure
        color: theme.background
        opacity: 0.55
    }

    Row {
        anchors.centerIn: art
        visible: !ui.playing && !ui.hasPlaybackFailure
        spacing: root.artSize * 0.07

        Rectangle {
            width: root.artSize * 0.07
            height: root.artSize * 0.26
            radius: width / 2
            color: theme.ink
        }
        Rectangle {
            width: root.artSize * 0.07
            height: root.artSize * 0.26
            radius: width / 2
            color: theme.ink
        }
    }
}
