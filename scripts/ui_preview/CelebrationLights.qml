import QtQuick

// A handful of light points leaving a centre, for the two moments AQENO has
// that deserve one: a message arriving and a timer completing.
//
// Seven fixed Items with declarative positions — no particle system. The brief
// asks for perceptual equivalence at the lowest cost, and at this scale a
// simulation would buy nothing a person could see (brief, "message
// celebration"). Their variation is derived from the index, not from a random
// number, so the same `phase` always renders the same frame and a still is
// reviewable.
//
// Everything is driven by `phase` rather than by an internal timeline, which is
// what lets a screen scrub it, replay it, or hold it at rest.
Item {
    id: root

    property var theme
    property color tint: theme ? theme.accent : "#23d5b6"
    property real phase: 0
    property int count: 7
    // Where the points start and end, as a share of the item's half-size.
    property real from: 0.42
    property real to: 1.0

    Repeater {
        model: root.count

        delegate: Rectangle {
            // Spread unevenly on purpose: a perfect ring of dots reads as a
            // loading spinner rather than as light.
            readonly property real angle: (index / root.count) * 2 * Math.PI
                + (index % 3) * 0.21 - 0.7
            readonly property real lateness: (index % 4) * 0.07
            readonly property real local: Math.max(0, Math.min(1,
                (root.phase - lateness) / Math.max(0.01, 1 - lateness)))
            readonly property real eased: 1 - Math.pow(1 - local, 3)
            readonly property real reach: (root.from + (root.to - root.from) * eased)
                * Math.min(root.width, root.height) / 2

            width: Math.max(3, Math.min(root.width, root.height) * (0.035 - (index % 3) * 0.006))
            height: width
            radius: width / 2
            color: root.tint

            x: root.width / 2 - width / 2 + Math.cos(angle) * reach
            y: root.height / 2 - height / 2 + Math.sin(angle) * reach
            // Rise quickly, leave slowly, end at nothing: the moment passes
            // rather than settling into permanent decoration (P19).
            opacity: local <= 0 ? 0 : Math.min(1, local * 5) * (1 - local) * 1.6
        }
    }
}
