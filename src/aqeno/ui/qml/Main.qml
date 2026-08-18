import QtQuick 2.15
import QtQuick.Window 2.15

Window {
    id: window
    visible: false
    visibility: Window.FullScreen
    color: "#0b0f14"
    title: "AQENO"

    readonly property color ink: "#f5f7fa"
    readonly property color mutedInk: "#a8b0bd"
    readonly property color surfaceColor: "#171d26"
    readonly property color accent: "#8ed7c2"
    readonly property color warning: "#f1bd78"

    Item {
        objectName: "surface"
        anchors.fill: parent
        visible: deviceUi.displayState !== "off"

        Item {
            id: home
            anchors.fill: parent
            visible: deviceUi.displayState === "interactive" && deviceUi.surface === "home"

            Item {
                id: brandMark
                width: 52
                height: 52
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.leftMargin: Math.max(36, parent.width * 0.045)
                anchors.topMargin: Math.max(28, parent.height * 0.05)

                Rectangle {
                    width: 18
                    height: 42
                    radius: 9
                    color: window.accent
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }
                Rectangle {
                    width: 18
                    height: 28
                    radius: 9
                    color: "#71a9db"
                    anchors.centerIn: parent
                }
                Rectangle {
                    width: 18
                    height: 36
                    radius: 9
                    color: "#d99cbb"
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                }
            }

            GridView {
                id: libraryGrid
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.leftMargin: Math.max(36, parent.width * 0.045)
                anchors.rightMargin: anchors.leftMargin
                anchors.topMargin: Math.max(104, parent.height * 0.17)
                anchors.bottomMargin: Math.max(36, parent.height * 0.06)
                cellWidth: width / Math.max(1, Math.min(3, count))
                cellHeight: height
                interactive: false
                model: deviceUi.tiles

                delegate: Item {
                    width: libraryGrid.cellWidth
                    height: libraryGrid.cellHeight
                    scale: tileTap.pressed ? 0.975 : 1.0

                    Behavior on scale {
                        NumberAnimation { duration: 90 }
                    }

                    Rectangle {
                        id: card
                        anchors.fill: parent
                        anchors.margins: Math.max(10, parent.width * 0.035)
                        radius: Math.max(22, width * 0.055)
                        color: window.surfaceColor
                        border.width: contentId === deviceUi.nowPlayingContentId ? 5 : 1
                        border.color: contentId === deviceUi.nowPlayingContentId ? window.accent : "#28313f"
                        clip: true

                        Image {
                            anchors.fill: parent
                            visible: artworkUrl !== ""
                            source: artworkUrl
                            fillMode: Image.PreserveAspectCrop
                            asynchronous: true
                        }

                        Rectangle {
                            anchors.fill: parent
                            visible: artworkUrl === ""
                            color: "#24303b"

                            Text {
                                anchors.centerIn: parent
                                text: "♪"
                                color: window.mutedInk
                                font.pixelSize: Math.max(64, parent.height * 0.22)
                            }
                        }

                        Rectangle {
                            width: Math.max(58, parent.width * 0.18)
                            height: width
                            radius: width / 2
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            anchors.margins: 18
                            visible: contentId === deviceUi.nowPlayingContentId
                            color: window.accent

                            Item {
                                anchors.centerIn: parent
                                width: parent.width * 0.34
                                height: parent.height * 0.34

                                Rectangle {
                                    width: parent.width * 0.28
                                    height: parent.height
                                    radius: width / 2
                                    color: "#10241f"
                                    visible: deviceUi.playing
                                }
                                Rectangle {
                                    width: parent.width * 0.28
                                    height: parent.height
                                    radius: width / 2
                                    color: "#10241f"
                                    anchors.right: parent.right
                                    visible: deviceUi.playing
                                }
                                Canvas {
                                    anchors.fill: parent
                                    visible: !deviceUi.playing
                                    onPaint: {
                                        var ctx = getContext("2d")
                                        ctx.reset()
                                        ctx.fillStyle = "#10241f"
                                        ctx.beginPath()
                                        ctx.moveTo(width * 0.2, 0)
                                        ctx.lineTo(width, height * 0.5)
                                        ctx.lineTo(width * 0.2, height)
                                        ctx.closePath()
                                        ctx.fill()
                                    }
                                }
                            }
                        }

                        TapHandler {
                            id: tileTap
                            onTapped: deviceUi.selectContent(contentId)
                        }
                    }
                }
            }

            Item {
                anchors.centerIn: parent
                width: Math.min(parent.width * 0.7, 560)
                height: 260
                visible: deviceUi.libraryEmpty

                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: "♪"
                    color: window.accent
                    font.pixelSize: 112
                }
                Text {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    text: qsTr("Nothing here yet")
                    color: window.mutedInk
                    font.pixelSize: 32
                }
            }
        }

        Item {
            id: nowPlaying
            anchors.fill: parent
            visible: deviceUi.displayState === "interactive" && deviceUi.surface === "now_playing"

            Rectangle {
                id: homeButton
                width: Math.max(84, Math.min(parent.width, parent.height) * 0.13)
                height: width
                radius: width / 2
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.margins: Math.max(28, parent.height * 0.05)
                color: homeTap.pressed ? "#303b49" : window.surfaceColor
                border.width: 1
                border.color: "#344050"

                Canvas {
                    anchors.centerIn: parent
                    width: parent.width * 0.42
                    height: parent.height * 0.42
                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()
                        ctx.strokeStyle = window.ink
                        ctx.lineWidth = Math.max(4, width * 0.11)
                        ctx.lineCap = "round"
                        ctx.lineJoin = "round"
                        ctx.beginPath()
                        ctx.moveTo(width * 0.08, height * 0.48)
                        ctx.lineTo(width * 0.5, height * 0.12)
                        ctx.lineTo(width * 0.92, height * 0.48)
                        ctx.moveTo(width * 0.2, height * 0.4)
                        ctx.lineTo(width * 0.2, height * 0.9)
                        ctx.lineTo(width * 0.8, height * 0.9)
                        ctx.lineTo(width * 0.8, height * 0.4)
                        ctx.stroke()
                    }
                }

                TapHandler {
                    id: homeTap
                    onTapped: deviceUi.showHome()
                }
            }

            Rectangle {
                id: artworkFrame
                width: Math.min(parent.width * 0.42, parent.height * 0.68)
                height: width
                radius: Math.max(24, width * 0.07)
                anchors.left: parent.left
                anchors.leftMargin: parent.width * 0.15
                anchors.verticalCenter: parent.verticalCenter
                color: window.surfaceColor
                clip: true

                Image {
                    anchors.fill: parent
                    visible: deviceUi.nowPlayingArtworkUrl !== ""
                    source: deviceUi.nowPlayingArtworkUrl
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                }

                Text {
                    anchors.centerIn: parent
                    visible: deviceUi.nowPlayingArtworkUrl === ""
                    text: "♪"
                    color: window.mutedInk
                    font.pixelSize: Math.max(72, parent.height * 0.24)
                }
            }

            Item {
                anchors.left: artworkFrame.right
                anchors.leftMargin: parent.width * 0.07
                anchors.right: parent.right
                anchors.rightMargin: parent.width * 0.07
                anchors.verticalCenter: parent.verticalCenter
                height: artworkFrame.height * 0.78

                Text {
                    id: titleText
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    text: deviceUi.nowPlayingTitle
                    color: window.ink
                    font.pixelSize: Math.max(38, window.height * 0.075)
                    font.weight: Font.DemiBold
                    wrapMode: Text.Wrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }

                Text {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: titleText.bottom
                    anchors.topMargin: 14
                    visible: deviceUi.nowPlayingChapter !== ""
                    text: deviceUi.nowPlayingChapter
                    color: window.mutedInk
                    font.pixelSize: Math.max(22, window.height * 0.038)
                    elide: Text.ElideRight
                }

                Rectangle {
                    id: statusPill
                    anchors.left: parent.left
                    anchors.bottom: progressTrack.top
                    anchors.bottomMargin: 28
                    width: statusRow.width + 34
                    height: 58
                    radius: height / 2
                    color: deviceUi.hasPlaybackFailure ? "#3d3022" : "#17352e"

                    Row {
                        id: statusRow
                        anchors.centerIn: parent
                        spacing: 14

                        Item {
                            width: 20
                            height: 24

                            Rectangle {
                                width: 6
                                height: parent.height
                                radius: 3
                                color: deviceUi.hasPlaybackFailure ? window.warning : window.accent
                                visible: deviceUi.playing && !deviceUi.hasPlaybackFailure
                            }
                            Rectangle {
                                width: 6
                                height: parent.height
                                radius: 3
                                anchors.right: parent.right
                                color: window.accent
                                visible: deviceUi.playing && !deviceUi.hasPlaybackFailure
                            }
                            Text {
                                anchors.centerIn: parent
                                visible: !deviceUi.playing || deviceUi.hasPlaybackFailure
                                text: deviceUi.hasPlaybackFailure ? "!" : "▶"
                                color: deviceUi.hasPlaybackFailure ? window.warning : window.accent
                                font.pixelSize: 24
                                font.weight: Font.Bold
                            }
                        }

                        Text {
                            text: deviceUi.hasPlaybackFailure ? qsTr("That did not work")
                                                              : deviceUi.playing ? qsTr("Playing")
                                                                                 : qsTr("Paused")
                            color: deviceUi.hasPlaybackFailure ? window.warning : window.accent
                            font.pixelSize: 24
                            font.weight: Font.DemiBold
                        }
                    }
                }

                Rectangle {
                    id: progressTrack
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 8
                    radius: 4
                    color: "#29313d"

                    Rectangle {
                        width: parent.width * deviceUi.progress
                        height: parent.height
                        radius: parent.radius
                        color: window.accent
                    }
                }
            }
        }

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
