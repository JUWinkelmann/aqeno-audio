import QtQuick 2.15

// Artwork with AQENO's own fallback. Never a file, folder or Linux icon
// (DEVICE_UI_BLUEPRINT.md § Visual language).
//
// Covers are square by design and the frame carries a small radius. A masked
// rounded crop was tried and rejected: it renders as an empty black square
// inside a Repeater delegate on this Qt build, and a cover that does not appear
// is a worse product than a cover with tighter corners.
Rectangle {
    id: frame

    property var theme
    property string source: ""
    property real cornerRadius: theme ? theme.radiusSm : 12

    radius: cornerRadius
    color: theme ? theme.surface : "#12171d"
    clip: true

    Image {
        anchors.fill: parent
        visible: frame.source !== ""
        source: frame.source
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        cache: true
    }

    // A calm mark rather than a broken-image glyph: three rounded strokes, the
    // same shape family as the AQENO brand mark.
    Row {
        anchors.centerIn: parent
        visible: frame.source === ""
        spacing: Math.max(4, frame.width * 0.035)

        Rectangle {
            width: Math.max(6, frame.width * 0.045)
            height: Math.max(18, frame.height * 0.16)
            radius: width / 2
            color: theme ? theme.hairline : "#2b343e"
            anchors.verticalCenter: parent.verticalCenter
        }
        Rectangle {
            width: Math.max(6, frame.width * 0.045)
            height: Math.max(28, frame.height * 0.26)
            radius: width / 2
            color: theme ? theme.hairline : "#2b343e"
            anchors.verticalCenter: parent.verticalCenter
        }
        Rectangle {
            width: Math.max(6, frame.width * 0.045)
            height: Math.max(22, frame.height * 0.2)
            radius: width / 2
            color: theme ? theme.hairline : "#2b343e"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}
