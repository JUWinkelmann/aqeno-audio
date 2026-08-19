import QtQuick

// Artwork, title, context, progress — and nothing else. The five physical
// controls already carry Previous, Next, Volume, Play/Pause and Home, so no
// virtual transport row exists (brief § 13, PRODUCT_FOUNDATION.md P20).
//
// One vertical hierarchy at every size. The artwork is the object; everything
// below it is caption. Splitting it left/right made a wide panel look like a
// media player window rather than a thing playing something.
Item {
    id: root

    property var theme
    property var ui

    readonly property real artSize: Math.min(
        width * 0.42, height * (theme.showsDetails ? 0.46 : 0.54))

    Column {
        id: stack
        anchors.horizontalCenter: parent.horizontalCenter
        y: (root.height - height) / 2
        width: Math.min(root.width * 0.66, 620 * theme.unit)
        spacing: theme.spaceMd

        ArtworkFrame {
            id: art
            anchors.horizontalCenter: parent.horizontalCenter
            theme: root.theme
            source: ui.nowPlayingArtworkUrl
            width: root.artSize
            height: root.artSize

            // The cover lends its colour to the light around it. With no
            // artwork there is no invented colour: the surface simply stays
            // dark (brief § 14, § 44).
            ArtworkGlow {
                anchors.fill: parent
                theme: root.theme
                cornerRadius: parent.cornerRadius
                tint: ui.nowPlayingAmbientColor !== "" ? ui.nowPlayingAmbientColor : theme.accent
                intensity: ui.nowPlayingAmbientColor !== ""
                    ? (ui.playing ? 1.0 : 0.4)
                    : 0.0
            }

            // Paused reads from the artwork itself: the cover recedes and one
            // large mark sits over it. Not a control — nothing here is
            // pressable, and the physical VOLUME press remains the only way to
            // resume. A corner chip was too quiet to notice from across a room,
            // which matters most for a person who cannot simply hear that the
            // audio stopped.
            Rectangle {
                anchors.fill: parent
                radius: parent.cornerRadius
                visible: !ui.playing && !ui.hasPlaybackFailure
                color: theme.background
                opacity: 0.62
            }

            AqenoGlyph {
                anchors.centerIn: parent
                width: parent.width * 0.3
                height: width
                visible: !ui.playing && !ui.hasPlaybackFailure
                theme: root.theme
                name: "pause"
                color: theme.ink
            }
        }

        Column {
            width: parent.width
            spacing: theme.spaceXs

            Text {
                width: parent.width
                visible: theme.showsLabels
                text: ui.nowPlayingTitle
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: theme.titleSize
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
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
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }

            // A failure is a state of this surface, never a modal dead end, and
            // it is phrased for the person rather than the log
            // (FAILURE_STATES.md).
            Text {
                width: parent.width
                visible: ui.hasPlaybackFailure
                text: theme.failureText(ui.failureCode)
                color: theme.attention
                font.family: theme.fontFamily
                font.pixelSize: theme.bodySize
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }

        Column {
            width: parent.width
            visible: !ui.hasPlaybackFailure
            spacing: theme.spaceSm

            ProgressTrack {
                width: parent.width
                theme: root.theme
                fraction: ui.progress
                live: ui.playing
            }

            Item {
                width: parent.width
                height: theme.captionSize
                visible: ui.durationText !== "" && theme.showsDetails

                Text {
                    anchors.left: parent.left
                    text: ui.positionText
                    color: theme.inkMuted
                    font.family: theme.fontFamily
                    font.pixelSize: theme.captionSize
                    font.features: theme.numericFeatures
                }
                Text {
                    anchors.right: parent.right
                    text: ui.durationText
                    color: theme.inkMuted
                    font.family: theme.fontFamily
                    font.pixelSize: theme.captionSize
                    font.features: theme.numericFeatures
                }
            }
        }
    }
}
