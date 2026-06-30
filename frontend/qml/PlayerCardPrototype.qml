import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    property var theme: playerCardBridge.styleColors

    RowLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 18

        TeamColumn {
            cards: playerCardBridge.leftPlayerCards
            theme: root.theme
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        TeamColumn {
            cards: playerCardBridge.rightPlayerCards
            theme: root.theme
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    component TeamColumn: Item {
        id: columnRoot
        property var cards: []
        property var theme: ({})

        ScrollView {
            anchors.fill: parent
            clip: true
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

            Column {
                width: parent.width
                spacing: 6

                Repeater {
                    model: cards

                    PlayerCard {
                        width: parent.width
                        height: 156
                        card: modelData
                        theme: columnRoot.theme
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
            }
        }
    }
}
