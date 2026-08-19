import QtQuick 2.15

// Home is not an app grid. One area is dominant; its neighbours are visible
// only as a hint that rotation has somewhere to go (ADR 0026, brief § 6).
Item {
    id: root

    property var theme
    property var ui

    readonly property int focusIndex: ui.focusedSectionIndex

    // --- empty library ---------------------------------------------------
    Column {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.8, 560 * theme.unit)
        spacing: theme.spaceMd
        visible: ui.libraryEmpty

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
            visible: !theme.compact
            text: qsTr("Inhalte werden im AQENO Client hinzugefügt.")
            color: theme.inkMuted
            font.family: theme.fontFamily
            font.pixelSize: theme.bodySize
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.Wrap
        }
    }

    // --- areas -----------------------------------------------------------
    Item {
        id: carousel
        anchors.fill: parent
        visible: !ui.libraryEmpty

        // The label band is reserved first; the artwork takes whatever is left.
        // That keeps the same hierarchy on a 4" panel instead of pushing the
        // caption off the bottom edge (brief § 7, § 31).
        readonly property real labelHeight: theme.titleSize * 1.35
            + (theme.compact ? 0 : theme.captionSize * 1.6)
        readonly property real available: height - labelHeight - theme.edge * 2
        readonly property real cardWidth: Math.max(
            80, Math.min(width * (theme.wide ? 0.42 : 0.6), available))
        readonly property real step: cardWidth + theme.spaceLg

        Row {
            id: row
            spacing: theme.spaceLg
            height: carousel.cardWidth
            y: theme.edge + (carousel.available - carousel.cardWidth) / 2
            x: parent.width / 2 - carousel.cardWidth / 2 - root.focusIndex * carousel.step

            Behavior on x {
                NumberAnimation { duration: theme.durationBase; easing.type: Easing.OutCubic }
            }

            Repeater {
                id: sectionRepeater
                model: ui.sections

                delegate: Item {
                    id: card
                    readonly property bool focused: model.sectionKey === ui.focusedSectionKey

                    width: carousel.cardWidth
                    height: carousel.cardWidth
                    opacity: focused ? 1.0 : 0.34
                    scale: focused ? 1.0 : 0.84

                    Behavior on opacity { NumberAnimation { duration: theme.durationBase } }
                    Behavior on scale { NumberAnimation { duration: theme.durationBase } }

                    // Focus is carried by four cues at once — size, opacity, a
                    // ring and the label weight below — so it never depends on
                    // colour alone and reads from across a room (ADR 0026 § 1).
                    Rectangle {
                        anchors.fill: art
                        anchors.margins: -theme.focusRingWidth * 1.5
                        radius: art.cornerRadius + theme.focusRingWidth * 1.5
                        visible: card.focused
                        color: "transparent"
                        border.width: theme.focusRingWidth
                        border.color: theme.ink
                    }

                    ArtworkFrame {
                        id: art
                        anchors.fill: parent
                        theme: root.theme
                        source: model.artworkUrl
                    }

                    TapHandler {
                        // Touch reaches the same action as a SELECT press and is
                        // never the only way there (ADR 0024 § 1).
                        onTapped: ui.openSection(model.sectionKey)
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
                text: theme.sectionTitle(ui.focusedSectionKey)
                color: theme.ink
                font.family: theme.fontFamily
                font.pixelSize: theme.titleSize
                font.weight: Font.DemiBold
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: !theme.compact
                text: qsTr("%1 verfügbar").arg(ui.focusedSectionCount)
                color: theme.inkMuted
                font.family: theme.fontFamily
                font.pixelSize: theme.captionSize
            }
        }
    }
}
