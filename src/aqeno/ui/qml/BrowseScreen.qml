import QtQuick 2.15

// One dominant item, neighbours only hinted. A library, never a file manager
// (brief § 8). PREVIOUS/NEXT are content order and deliberately do not reach
// this focus (ADR 0026 § 3).
Item {
    id: root

    property var theme
    property var ui

    Item {
        id: carousel
        anchors.fill: parent

        readonly property real labelHeight: (theme.showsLabels ? theme.titleSize * 1.35 : 0)
            + (theme.showsDetails && ui.itemCount > 1 ? theme.captionSize * 1.6 : 0)
        readonly property real available: height - labelHeight - theme.edge * 2
        readonly property real cardWidth: Math.max(
            80, Math.min(width * (theme.wide ? 0.4 : 0.58), available))
        readonly property real step: cardWidth + theme.spaceLg

        Row {
            id: row
            spacing: theme.spaceLg
            height: carousel.cardWidth
            y: theme.edge + (carousel.available - carousel.cardWidth) / 2
            x: parent.width / 2 - carousel.cardWidth / 2
               - Math.max(0, ui.focusedIndex - 1) * carousel.step

            Behavior on x {
                NumberAnimation { duration: theme.durationBase; easing.type: Easing.OutCubic }
            }

            Repeater {
                model: ui.tiles

                delegate: Item {
                    readonly property bool focused: model.contentId === ui.focusedContentId

                    width: carousel.cardWidth
                    height: carousel.cardWidth
                    opacity: focused ? 1.0 : 0.3
                    scale: focused ? 1.0 : 0.86

                    Behavior on opacity { NumberAnimation { duration: theme.durationBase } }
                    Behavior on scale { NumberAnimation { duration: theme.durationBase } }

                    Rectangle {
                        anchors.fill: cover
                        anchors.margins: -theme.focusRingWidth * 1.6
                        radius: cover.cornerRadius + theme.focusRingWidth * 1.6
                        visible: parent.focused
                        color: "transparent"
                        border.width: theme.focusRingWidth
                        border.color: theme.ink
                    }

                    ArtworkFrame {
                        id: cover
                        anchors.fill: parent
                        theme: root.theme
                        source: model.artworkUrl
                    }

                    // A quiet marker on whatever is currently playing, so
                    // returning to a list still says where you were.
                    Rectangle {
                        anchors.right: cover.right
                        anchors.bottom: cover.bottom
                        anchors.margins: theme.spaceSm
                        width: Math.round(18 * theme.unit)
                        height: width
                        radius: width / 2
                        visible: model.contentId === ui.nowPlayingContentId
                        color: theme.accent
                    }

                    TapHandler {
                        onTapped: ui.selectContent(model.contentId)
                    }
                }
            }
        }

        Column {
            anchors.bottom: parent.bottom
            anchors.bottomMargin: theme.edge
            anchors.horizontalCenter: parent.horizontalCenter
            width: parent.width - theme.edge * 2
            spacing: theme.spaceXs

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                visible: theme.showsLabels
                text: ui.focusedTitle
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: theme.titleSize
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: theme.showsDetails && ui.itemCount > 1
                text: ui.focusedIndex + " / " + ui.itemCount
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.captionSize
            }
        }
    }
}
