import QtQuick 2.15

// DIM is a materially reduced presentation, not Now Playing at lower
// brightness (ADR 0017 § 2). Glanceable: what is playing, nothing to operate.
Item {
    id: root

    property var theme
    property var ui

    readonly property real artSize: Math.min(root.width * 0.24, root.height * 0.42)

    ArtworkFrame {
        id: art
        theme: root.theme
        source: ui.nowPlayingArtworkUrl
        width: root.artSize
        height: root.artSize
        x: theme.edge * 1.6
        y: (root.height - root.artSize) / 2
    }

    Text {
        x: art.x + root.artSize + theme.spaceLg
        width: root.width - (art.x + root.artSize + theme.spaceLg) - theme.edge
        y: (root.height - height) / 2
        text: ui.nowPlayingTitle
        color: theme.inkMuted
        font.family: theme.fontFamily
        font.pixelSize: theme.bodySize
        wrapMode: Text.Wrap
        maximumLineCount: 2
        elide: Text.ElideRight
    }
}
