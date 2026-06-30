import QtQuick

Item {
    id: root

    property var theme: playerCardBridge.styleColors

    PlayerCard {
        anchors.fill: parent
        card: playerCardData
        theme: root.theme
        onOpenTracker: function(trackerUrl) {
            playerCardBridge.openTracker(trackerUrl)
        }
        onOpenVtl: function(vtlUrl) {
            playerCardBridge.openVtl(vtlUrl)
        }
        onCopyName: function(clipboardName) {
            playerCardBridge.copyName(clipboardName)
        }
        onOpenLoadout: function(playerKey) {
            playerCardBridge.openLoadout(playerKey)
        }
        onToggleFlag: function(puuid) {
            playerCardBridge.toggleFlag(puuid)
        }
    }
}
