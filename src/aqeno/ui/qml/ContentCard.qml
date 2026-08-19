import QtQuick

// The one card AQENO has. Home shows areas in it and Browse shows works in it,
// because they are the same act — one dominant thing, its neighbours only
// hinted (brief § 10, § 49).
//
// The card is a single object: a surface, the artwork inset within it, and the
// title on the surface below rather than printed over the image. That keeps
// `DEVICE_UI_BLUEPRINT.md`'s rule that content imagery carries no overlaid
// gradient or metadata, while still associating the title directly with the
// artwork the way the approved reference does.
Item {
    id: root

    property var theme
    property string title: ""
    property string subtitle: ""
    property string artworkUrl: ""
    property bool focused: false
    property bool marked: false

    readonly property real pad: theme ? theme.spaceSm : 12
    readonly property real artSize: Math.max(0, width - pad * 2)

    // Focus is four cues at once — scale, luminance, surface lift and the
    // suppression of everything beside it — so it never rests on colour and
    // reads from across a room (brief § 8, § 9).
    scale: focused ? (theme ? theme.focusScale : 1.0) : (theme ? theme.restScale : 0.82)
    opacity: focused ? 1.0 : (theme ? theme.restOpacity : 0.3)

    Behavior on scale {
        NumberAnimation {
            duration: root.theme ? root.theme.durationBase : 220
            easing.type: root.theme ? root.theme.easingStandard : Easing.OutCubic
        }
    }
    Behavior on opacity {
        NumberAnimation { duration: root.theme ? root.theme.durationBase : 220 }
    }

    PremiumSurface {
        anchors.fill: parent
        theme: root.theme
        focused: root.focused
        cornerRadius: root.theme ? root.theme.radiusLg : 34
    }

    ArtworkFrame {
        id: art
        theme: root.theme
        source: root.artworkUrl
        surroundColor: root.theme
            ? (root.focused ? root.theme.surfaceFocused : root.theme.surface)
            : "#080b0e"
        x: root.pad
        y: root.pad
        width: root.artSize
        height: root.artSize

        // A quiet mark on whatever is currently playing, so returning to a list
        // still says where you were.
        Rectangle {
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: root.pad
            width: Math.round(18 * (root.theme ? root.theme.unit : 1))
            height: width
            radius: width / 2
            visible: root.marked
            color: root.theme ? root.theme.accent : "#23d5b6"
        }
    }

    Column {
        id: label
        anchors.top: art.bottom
        anchors.bottom: parent.bottom
        anchors.left: art.left
        anchors.right: art.right
        spacing: root.theme ? root.theme.spaceXs : 6

        // Centred in whatever the artwork left over, so a one-line and a
        // two-line card still look like the same object.
        topPadding: Math.max(0, (height - implicitHeight) / 2)

        Text {
            width: parent.width
            visible: root.theme && root.theme.showsLabels && root.title !== ""
            text: root.title
            color: root.theme ? root.theme.ink : "#f4f7f9"
            font.family: root.theme ? root.theme.fontFamily : "Inter"
            font.pixelSize: root.theme ? root.theme.titleSize : 40
            font.weight: root.focused ? Font.DemiBold : Font.Medium
            horizontalAlignment: Text.AlignHCenter
            // A long title shrinks to fit rather than losing its ending. On a
            // shelf of covers the last word is often the one that identifies
            // the thing.
            fontSizeMode: Text.HorizontalFit
            minimumPixelSize: Math.round((root.theme ? root.theme.titleSize : 40) * 0.6)
            elide: Text.ElideRight
        }

        Text {
            width: parent.width
            visible: root.theme && root.theme.showsDetails && root.subtitle !== ""
            text: root.subtitle
            color: root.theme ? root.theme.inkMuted : "#8e9aa6"
            font.family: root.theme ? root.theme.fontFamily : "Inter"
            font.pixelSize: root.theme ? root.theme.captionSize : 20
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }

        // The lit base line: the focused card is the one the encoder is
        // holding. Present or absent rather than one colour against another,
        // so it still works for someone who sees no colour at all.
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            width: root.artSize * 0.42
            height: Math.max(3, Math.round(5 * (root.theme ? root.theme.unit : 1)))
            radius: height / 2
            opacity: root.focused ? 1.0 : 0.0
            color: root.theme ? root.theme.accent : "#23d5b6"

            Behavior on opacity {
                NumberAnimation { duration: root.theme ? root.theme.durationFast : 140 }
            }
        }
    }
}
