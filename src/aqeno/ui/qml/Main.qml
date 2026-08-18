import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    id: window
    // The composition root makes the first frame visible only after the
    // readiness ladder reaches UI_READY.
    visible: false
    visibility: Window.FullScreen
    color: "#101114"
    title: "AQENO"

    // The panel adapter owns authoritative OFF.  Keeping the scene empty here
    // also makes a software/compositor wake harmless rather than a flash.
    Item {
        objectName: "surface"
        anchors.fill: parent
        visible: deviceUi.displayState !== "off"

        GridView {
            id: libraryGrid
            anchors.fill: parent
            anchors.margins: Math.max(24, Math.min(parent.width, parent.height) * 0.06)
            visible: deviceUi.displayState === "interactive" && deviceUi.surface === "home"
            cellWidth: width / 3
            cellHeight: height
            interactive: false
            model: deviceUi.tiles

            delegate: Item {
                width: libraryGrid.cellWidth
                height: libraryGrid.cellHeight

                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 12
                    radius: 18
                    color: "#292d37"

                    Image {
                        anchors.fill: parent
                        anchors.margins: 4
                        visible: artworkUrl !== ""
                        source: artworkUrl
                        fillMode: Image.PreserveAspectCrop
                        asynchronous: true
                    }

                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 32
                        visible: artworkUrl === ""
                        text: title
                        color: "white"
                        font.pixelSize: Math.max(24, parent.height * 0.07)
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.WordWrap
                    }

                    TapHandler {
                        // The surface is absent in OFF and DIM, so the touch
                        // that wakes the panel cannot select a tile. DIM has
                        // no TapHandler at all (ADR 0016).
                        onTapped: deviceUi.selectContent(contentId)
                    }
                }
            }
        }

        Item {
            id: nowPlaying
            anchors.fill: parent
            visible: deviceUi.displayState === "interactive" && deviceUi.surface === "now_playing"

            Image {
                anchors.centerIn: parent
                width: Math.min(parent.width * 0.42, parent.height * 0.62)
                height: width
                visible: deviceUi.nowPlayingArtworkUrl !== ""
                source: deviceUi.nowPlayingArtworkUrl
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.16
                width: parent.width * 0.8
                text: deviceUi.nowPlayingTitle
                color: "white"
                font.pixelSize: Math.max(28, parent.height * 0.07)
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }

            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: parent.height * 0.09
                width: parent.width * 0.8
                visible: deviceUi.nowPlayingChapter !== ""
                text: deviceUi.nowPlayingChapter
                color: "#c6cad3"
                font.pixelSize: Math.max(18, parent.height * 0.035)
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }
        }

        // DIM intentionally contains no controls or navigation. It is a
        // glanceable presentation, not a dimmed copy of the interactive UI.
        Item {
            anchors.fill: parent
            visible: deviceUi.displayState === "dim"

            Image {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: parent.width * 0.12
                width: Math.min(parent.height * 0.48, parent.width * 0.3)
                height: width
                visible: deviceUi.nowPlayingArtworkUrl !== ""
                source: deviceUi.nowPlayingArtworkUrl
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }

            Text {
                anchors.left: parent.left
                anchors.leftMargin: parent.width * 0.48
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                text: deviceUi.nowPlayingTitle
                color: "#e5e7ec"
                font.pixelSize: Math.max(24, parent.height * 0.055)
                elide: Text.ElideRight
            }
        }
    }
}
