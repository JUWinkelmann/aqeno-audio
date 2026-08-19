import QtQuick

// Artwork as an object rather than an image (brief § 13): a generous
// proportional radius, a hairline of caught light around the edge, and AQENO's
// own fallback. Never a file, folder or Linux icon
// (DEVICE_UI_BLUEPRINT.md § Visual language).
//
// Covers are square by design. `clip` is rectangular on this Qt build — a
// rounded Rectangle clips its children to the bounding box, not to the
// silhouette — and a real mask renders as an empty black square inside a
// Repeater delegate. So the corners are *covered* instead of masked: four
// slivers of the surrounding colour, one triangulated Shape, no shader and no
// per-frame cost.
Item {
    id: frame

    property var theme
    property string source: ""
    property real cornerRadius: theme ? theme.artworkRadius(Math.min(width, height)) : 12
    // What the corners fall back to. The artwork sits on black on its own and
    // on a card surface inside one, and the cover has to agree with whichever.
    property color surroundColor: theme ? theme.background : "#000000"

    Rectangle {
        anchors.fill: parent
        radius: frame.cornerRadius
        color: frame.theme ? frame.theme.surface : "#080b0e"
        clip: true

        Image {
            anchors.fill: parent
            visible: frame.source !== ""
            source: frame.source
            fillMode: Image.PreserveAspectCrop
            asynchronous: false
            cache: true
        }

        // Without artwork the frame stays part of the same material rather than
        // becoming a hole: a quiet tonal ground and one calm mark — three
        // rounded strokes, the shape family of the AQENO brand mark
        // (brief § 44).
        Rectangle {
            anchors.fill: parent
            visible: frame.source === ""
            gradient: Gradient {
                GradientStop { position: 0.0; color: frame.theme ? frame.theme.surfaceRaised : "#1a2028" }
                GradientStop { position: 1.0; color: frame.theme ? frame.theme.surface : "#080b0e" }
            }
        }

        Row {
            anchors.centerIn: parent
            visible: frame.source === ""
            spacing: Math.max(4, frame.width * 0.035)

            Rectangle {
                width: Math.max(6, frame.width * 0.045)
                height: Math.max(18, frame.height * 0.16)
                radius: width / 2
                color: frame.theme ? frame.theme.hairline : "#2b343e"
                anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                width: Math.max(6, frame.width * 0.045)
                height: Math.max(28, frame.height * 0.26)
                radius: width / 2
                color: frame.theme ? frame.theme.hairline : "#2b343e"
                anchors.verticalCenter: parent.verticalCenter
            }
            Rectangle {
                width: Math.max(6, frame.width * 0.045)
                height: Math.max(22, frame.height * 0.2)
                radius: width / 2
                color: frame.theme ? frame.theme.hairline : "#2b343e"
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    RoundedCorners {
        anchors.fill: parent
        cornerRadius: frame.cornerRadius
        color: frame.surroundColor
    }

    // The caught edge. One hairline, no scrim over the image: the blueprint's
    // rule that content imagery carries no overlaid gradient stands.
    Rectangle {
        anchors.fill: parent
        radius: frame.cornerRadius
        color: "transparent"
        border.width: Math.max(1, Math.round(frame.theme ? frame.theme.unit : 1))
        border.color: frame.theme ? frame.theme.edgeLight : Qt.rgba(1, 1, 1, 0.10)
    }
}
