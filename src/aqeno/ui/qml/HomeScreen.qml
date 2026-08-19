import QtQuick

// Home is not an app grid. One area is dominant; its neighbours are visible
// only as a hint that rotation has somewhere to go (ADR 0026, brief § 6).
Item {
    id: root

    property var theme
    property var ui

    readonly property int focusIndex: ui.focusedSectionIndex

    // --- empty library ---------------------------------------------------
    Item {
        anchors.fill: parent
        visible: ui.libraryEmpty

        Column {
            anchors.centerIn: parent
            width: Math.min(parent.width * 0.8, 560 * theme.unit)
            spacing: theme.spaceMd

            // Nothing to play is still a state of the product, not a fault: the
            // same frame every cover uses, lit just enough to look deliberate.
            // Neutral rather than mint — nothing here is live (brief § 44).
            ArtworkFrame {
                anchors.horizontalCenter: parent.horizontalCenter
                theme: root.theme
                width: Math.min(parent.width * 0.42, root.height * 0.34)
                height: width

                ArtworkGlow {
                    anchors.fill: parent
                    theme: root.theme
                    cornerRadius: parent.cornerRadius
                    tint: theme.inkMuted
                    intensity: 0.5
                }
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: qsTr("Noch nichts zum Hören")
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: theme.titleSize
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: parent.width
                visible: theme.showsDetails
                text: qsTr("Inhalte werden im AQENO Client hinzugefügt.")
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.bodySize
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.Wrap
            }
        }
    }

    // --- areas -----------------------------------------------------------
    Item {
        id: carousel
        anchors.fill: parent
        visible: !ui.libraryEmpty

        // The label band is reserved first; the card takes whatever is left.
        // That keeps the same hierarchy on a 4" panel instead of pushing the
        // caption off the bottom edge (brief § 42, § 43).
        readonly property real labelBand: theme.cardLabelBand()
        readonly property real available: height - theme.edge * 2
            - indicator.height - theme.spaceMd
        readonly property real cardWidth: Math.max(
            80, Math.min(width * 0.55, available - theme.spaceSm - labelBand))
        readonly property real cardHeight: cardWidth + theme.spaceSm + labelBand

        // The next card's near edge sits this far inside the screen edge, so
        // rotation visibly has somewhere to go without a second card competing
        // for attention.
        readonly property real step: width / 2 - width * 0.11
            + cardWidth * theme.restScale / 2

        Row {
            id: row
            height: carousel.cardHeight
            y: theme.edge + (carousel.available - carousel.cardHeight) / 2
            x: parent.width / 2 - carousel.cardWidth / 2 - root.focusIndex * carousel.step
            spacing: carousel.step - carousel.cardWidth

            // State-driven, so it always converges on the latest focus. Several
            // fast detents retarget this one animation instead of queueing a
            // sequence, and no detent is lost (brief § 12).
            Behavior on x {
                NumberAnimation {
                    duration: theme.durationBase
                    easing.type: theme.easingEmphasis
                }
            }

            Repeater {
                id: sectionRepeater
                model: ui.sections

                delegate: ContentCard {
                    width: carousel.cardWidth
                    height: carousel.cardHeight
                    theme: root.theme
                    focused: model.sectionKey === ui.focusedSectionKey
                    title: theme.sectionTitle(model.sectionKey)
                    subtitle: qsTr("%1 verfügbar").arg(model.itemCount)
                    artworkUrl: model.artworkUrl

                    TapHandler {
                        // Touch reaches the same action as a SELECT press and is
                        // never the only way there (ADR 0024 § 1).
                        onTapped: ui.openSection(model.sectionKey)
                    }
                }
            }
        }

        PageIndicator {
            id: indicator
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: theme.edge
            theme: root.theme
            count: sectionRepeater.count
            index: root.focusIndex
        }
    }
}
