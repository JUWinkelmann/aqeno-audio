import QtQuick
import QtQuick.Window
import "../../src/aqeno/ui/qml"

// Hosts one design-target screen at a given viewport. The screen name arrives as
// the `previewScreen` context property; the shared Theme is handed to the loaded
// item so a design decision here is the same decision the product inherits.
Window {
    id: window
    visible: false
    width: 800
    height: 480
    color: theme.background
    title: "AQENO design target"

    Theme {
        id: theme
        viewportWidth: window.width
        viewportHeight: window.height
    }

    Loader {
        id: loader
        anchors.fill: parent
        source: previewScreen + ".qml"
        onLoaded: item.theme = theme
    }
}
