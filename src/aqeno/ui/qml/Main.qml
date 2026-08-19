import QtQuick 2.15
import QtQuick.Window 2.15

// The AQENO device surface.
//
//   THE DISPLAY SHOWS. THE HARDWARE OPERATES.
//
// Every path here is reachable with SELECT, PREVIOUS, NEXT, VOLUME and HOME
// alone (ADR 0026 § 2). Touch mirrors those actions and is never required.
// Which state is visible is decided by the display machine and the application
// surface — this file routes, it does not decide.
Window {
    id: window
    visible: false
    visibility: Window.FullScreen
    color: theme.background
    title: "AQENO"

    Theme {
        id: theme
        viewportWidth: window.width
        viewportHeight: window.height
    }

    Item {
        id: surface
        objectName: "surface"
        anchors.fill: parent

        // OFF means no intended visible output at all: no clock, no logo, no
        // status, no glow (DISPLAY_STATE_MACHINE.md invariant 9). Removing the
        // surface also takes it out of hit testing.
        visible: deviceUi.displayState !== "off"

        Item {
            id: interactive
            anchors.fill: parent
            visible: deviceUi.displayState === "interactive"
                     || deviceUi.displayState === "setup"

            HomeScreen {
                anchors.fill: parent
                visible: deviceUi.surface === "home"
                theme: theme
                ui: deviceUi
            }

            BrowseScreen {
                anchors.fill: parent
                visible: deviceUi.surface === "browse"
                theme: theme
                ui: deviceUi
            }

            NowPlayingScreen {
                anchors.fill: parent
                visible: deviceUi.surface === "now_playing"
                theme: theme
                ui: deviceUi
            }
        }

        DimScreen {
            anchors.fill: parent
            visible: deviceUi.displayState === "dim"
            theme: theme
            ui: deviceUi
        }

        // Overlays ride above whatever is showing, and only while something is
        // showing: neither of them may light a dark panel.
        VolumeOverlay {
            id: volumeOverlay
            anchors.fill: parent
            visible: deviceUi.displayState === "interactive"
            theme: theme
            ui: deviceUi
        }

        NoticeOverlay {
            id: notice
            anchors.fill: parent
            visible: deviceUi.displayState === "interactive"
            theme: theme
        }

        Connections {
            target: deviceUi
            function onUnassignedTag() {
                // Only while the panel is already lit. In the dark, an
                // unassigned token deliberately does nothing at all
                // (DISPLAY_STATE_MACHINE.md note 7).
                if (deviceUi.displayState !== "interactive")
                    return
                notice.show(qsTr("Dieses Objekt gehört noch zu nichts."))
            }
        }
    }
}
