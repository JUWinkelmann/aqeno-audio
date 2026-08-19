import QtQuick

// Where you are in a carousel, without a number and without reading (brief
// § 10). Deliberately bounded: beyond `maximumDots` the marks stop being one
// per item and become a coarse position, because twenty-four dots say less
// than four do.
Item {
    id: root

    property var theme
    property int count: 0
    property int index: 0
    property int maximumDots: 5

    readonly property int dots: Math.min(count, maximumDots)
    readonly property int activeDot: count <= maximumDots
        ? index
        : Math.round(index / Math.max(1, count - 1) * (maximumDots - 1))

    readonly property real dotSize: Math.max(5, Math.round(9 * (theme ? theme.unit : 1)))

    visible: count > 1
    implicitWidth: row.width
    implicitHeight: dotSize

    Row {
        id: row
        anchors.centerIn: parent
        spacing: root.dotSize * 1.1

        Repeater {
            model: root.dots

            delegate: Rectangle {
                readonly property bool current: index === root.activeDot

                width: root.dotSize
                height: root.dotSize
                radius: width / 2
                anchors.verticalCenter: parent.verticalCenter
                color: current
                    ? (root.theme ? root.theme.accent : "#23d5b6")
                    : (root.theme ? root.theme.track : "#232a32")
                // Position is also carried by size, so the mark survives
                // without colour perception (brief § 9).
                scale: current ? 1.0 : 0.78

                Behavior on color { ColorAnimation { duration: root.theme ? root.theme.durationFast : 140 } }
                Behavior on scale { NumberAnimation { duration: root.theme ? root.theme.durationFast : 140 } }
            }
        }
    }
}
