import QtQuick

// One dominant item, neighbours only hinted. A library, never a file manager
// (brief § 8). PREVIOUS/NEXT are content order and deliberately do not reach
// this focus (ADR 0026 § 3).
Item {
    id: root

    property var theme
    property var ui

    readonly property int focusIndex: Math.max(0, ui.focusedIndex - 1)

    Item {
        id: carousel
        anchors.fill: parent

        readonly property real labelBand: theme.cardLabelBand()
        readonly property real available: height - theme.edge * 2
            - indicator.height - theme.spaceMd
        readonly property real cardWidth: Math.max(
            80, Math.min(width * 0.55, available - theme.spaceSm - labelBand))
        readonly property real cardHeight: cardWidth + theme.spaceSm + labelBand
        readonly property real step: width / 2 - width * 0.11
            + cardWidth * theme.restScale / 2

        Row {
            id: row
            height: carousel.cardHeight
            y: theme.edge + (carousel.available - carousel.cardHeight) / 2
            x: parent.width / 2 - carousel.cardWidth / 2 - root.focusIndex * carousel.step
            spacing: carousel.step - carousel.cardWidth

            Behavior on x {
                NumberAnimation {
                    duration: theme.durationBase
                    easing.type: theme.easingEmphasis
                }
            }

            Repeater {
                id: tileRepeater
                model: ui.tiles

                delegate: ContentCard {
                    width: carousel.cardWidth
                    height: carousel.cardHeight
                    theme: root.theme
                    focused: model.contentId === ui.focusedContentId
                    title: model.title
                    artworkUrl: model.artworkUrl
                    marked: model.contentId === ui.nowPlayingContentId

                    TapHandler {
                        onTapped: ui.selectContent(model.contentId)
                    }
                }
            }
        }

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: theme.edge
            spacing: theme.spaceMd

            PageIndicator {
                id: indicator
                anchors.verticalCenter: parent.verticalCenter
                theme: root.theme
                count: tileRepeater.count
                index: root.focusIndex
            }

            // The dots place you; the count says exactly where, for someone who
            // wants exactly. It stays out of a header bar — AQENO is a device,
            // not an app (brief § 46).
            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: theme.showsDetails && ui.itemCount > 1
                text: ui.focusedIndex + " / " + ui.itemCount
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.captionSize
                font.features: theme.numericFeatures
            }
        }
    }
}
