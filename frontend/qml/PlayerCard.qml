import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var card: ({})
    property var theme: ({})
    signal openTracker(string trackerUrl)
    signal openVtl(string vtlUrl)
    signal copyName(string clipboardName)
    signal openLoadout(string playerKey)
    signal toggleFlag(string puuid)

    implicitHeight: 156
    height: 156
    radius: 16
    color: cardMouse.containsMouse
        ? (card.isFlagged ? value("flaggedRowHover") : value("cardAlt"))
        : (card.isFlagged ? value("flaggedRow") : value("card"))
    border.color: card.isFlagged ? value("flaggedBorder") : (cardMouse.containsMouse ? value("border") : value("borderSoft"))
    border.width: 1
    clip: true

    function value(key) {
        return theme && theme[key] ? theme[key] : "transparent"
    }

    function imageSource(path) {
        if (!path) {
            return ""
        }
        var normalized = String(path).replace(/\\/g, "/")
        if (normalized.indexOf("file:/") === 0 || normalized.indexOf("qrc:/") === 0) {
            return normalized
        }
        return "file:///" + normalized
    }

    function alphaColor(color, alpha) {
        var parsed = Qt.color(color || value("card"))
        return Qt.rgba(parsed.r, parsed.g, parsed.b, alpha)
    }

    function toneColor(tone, numericValue) {
        if (tone === "positive" || Number(numericValue) > 0) {
            return value("teal")
        }
        if (tone === "negative" || Number(numericValue) < 0) {
            return value("red")
        }
        return alphaColor(value("muted"), 0.72)
    }

    function statColor(tone, textValue) {
        if (String(textValue || "").toUpperCase() === "N/A") {
            return value("muted")
        }
        if (tone === "red" || tone === "negative") {
            return value("red")
        }
        if (tone === "gold" || tone === "warning") {
            return value("gold")
        }
        if (tone === "limegreen" || tone === "positive" || tone === "good") {
            return value("teal")
        }
        if (tone === "cyan" || tone === "informational") {
            return value("cyan")
        }
        return value("text")
    }

    MouseArea {
        id: cardMouse
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 12
        anchors.rightMargin: 4
        anchors.topMargin: 7
        anchors.bottomMargin: 7
        spacing: 18

        Item {
            Layout.preferredWidth: 142
            Layout.preferredHeight: 142

            Rectangle {
                anchors.fill: parent
                radius: 12
                color: root.alphaColor(root.value("window"), 0.5)
                border.color: root.alphaColor(root.value("borderSoft"), 0.9)
                clip: true

                Image {
                    id: agentPortrait
                    anchors.fill: parent
                    anchors.margins: 1
                    source: root.imageSource(card.agentIconPath)
                    fillMode: Image.PreserveAspectFit
                    visible: status === Image.Ready
                }

                Text {
                    anchors.centerIn: parent
                    width: parent.width - 16
                    text: card.agentName || "Unknown"
                    color: root.value("muted")
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    visible: agentPortrait.status !== Image.Ready
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.margins: 2
                width: Math.max(30, levelText.implicitWidth + 8)
                height: 22
                radius: 4
                color: root.value("cyan")

                Text {
                    id: levelText
                    anchors.centerIn: parent
                    text: card.levelText || "N/A"
                    color: root.value("window")
                    font.pixelSize: 16
                    font.bold: true
                }
            }
        }

        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 260
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 28
                spacing: 8

                Text {
                    id: nameText
                    text: card.displayName || "Unknown"
                    color: nameMouse.containsMouse ? root.value("cyan") : root.value("text")
                    font.pixelSize: 20
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.maximumWidth: 260
                    Layout.fillWidth: true

                    MouseArea {
                        id: nameMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.openTracker(card.trackerUrl || "")
                    }
                }

                PlayerActionButton {
                    iconPath: card.copyIconPath || ""
                    fallbackText: "C"
                    tooltipText: "Copy " + (card.clipboardName || "")
                    theme: root.theme
                    onClicked: root.copyName(card.clipboardName || "")
                }

                PlayerActionButton {
                    iconPath: card.vtlIconPath || ""
                    fallbackText: "V"
                    tooltipText: "View on VTL.lol"
                    theme: root.theme
                    onClicked: root.openVtl(card.vtlUrl || "")
                }

                PlayerActionButton {
                    iconPath: card.flagIconPath || ""
                    fallbackText: "F"
                    tooltipText: card.flagTooltip || "Toggle flagged player"
                    theme: root.theme
                    onClicked: root.toggleFlag(card.puuid || "")
                }

                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 48
                spacing: 12

                Rectangle {
                    id: weaponStrip
                    Layout.preferredWidth: 160
                    Layout.preferredHeight: 44
                    radius: 10
                    color: weaponMouse.containsMouse ? root.alphaColor(root.value("accentHover"), 0.16) : root.alphaColor(root.value("panel"), 0.72)
                    border.color: weaponMouse.containsMouse ? root.value("accentHover") : root.alphaColor(root.value("borderSoft"), 0.82)

                    Row {
                        anchors.centerIn: parent
                        spacing: 10

                        Repeater {
                            model: card.weaponIcons || []

                            Rectangle {
                                width: 65
                                height: 36
                                radius: 7
                                color: root.alphaColor(root.value("window"), 0.42)
                                border.color: root.alphaColor(root.value("borderSoft"), 0.75)

                                Image {
                                    anchors.fill: parent
                                    anchors.margins: 3
                                    source: root.imageSource(modelData.iconPath)
                                    fillMode: Image.PreserveAspectFit
                                    visible: status === Image.Ready
                                }

                                Text {
                                    anchors.centerIn: parent
                                    text: "-"
                                    color: root.value("muted")
                                    font.pixelSize: 14
                                    visible: !modelData.iconPath
                                }
                            }
                        }
                    }

                    MouseArea {
                        id: weaponMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.openLoadout(card.playerKey || card.clipboardName || "")
                    }
                }

                Text {
                    text: card.hasBuddyEquipped ? "Buddy" : ""
                    color: root.value("gold")
                    font.pixelSize: 11
                    font.bold: true
                    visible: card.hasBuddyEquipped
                }

                Text {
                    text: card.partyGroupId ? "Party " + card.partyGroupId : ""
                    color: root.value("accentHover")
                    font.pixelSize: 11
                    font.bold: true
                    visible: card.partyGroupId
                }

                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 5

                StatChip { label: "GAMES"; textValue: card.gamesText || "0"; tone: "neutral"; theme: root.theme }
                StatChip { label: "W/L"; textValue: card.winRateText || "N/A"; tone: card.winRateTone || "neutral"; theme: root.theme }
                StatChip { label: "ACS"; textValue: card.acsText || "N/A"; tone: card.acsTone || "neutral"; theme: root.theme }
                StatChip { label: "KD"; textValue: card.kdText || "N/A"; tone: card.kdTone || "neutral"; theme: root.theme }
                StatChip { label: "HS"; textValue: card.hsText || "N/A"; tone: card.hsTone || "neutral"; theme: root.theme }
                Item { Layout.fillWidth: true }
            }
        }

        Item {
            Layout.preferredWidth: 300
            Layout.fillHeight: true

            Row {
                id: recentRow
                anchors.left: parent.left
                anchors.top: parent.top
                spacing: 4

                Repeater {
                    model: card.ratingChanges || []

                    Rectangle {
                        width: 42
                        height: 42
                        radius: 21
                        color: root.toneColor(modelData.tone, modelData.numericValue)

                        Text {
                            anchors.centerIn: parent
                            text: modelData.valueText || modelData.text || "0"
                            color: modelData.tone === "positive" ? root.value("window") : root.value("text")
                            font.pixelSize: 12
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }

                        ToolTip.visible: recentMouse.containsMouse && (modelData.tooltip || "").length > 0
                        ToolTip.text: modelData.tooltip || ""
                        ToolTip.delay: 450

                        MouseArea {
                            id: recentMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            acceptedButtons: Qt.NoButton
                        }
                    }
                }
            }

            Row {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                spacing: 8

                Text {
                    width: Math.max(50, implicitWidth + 12)
                    height: 48
                    text: card.peakActText || "N/A"
                    color: root.value("muted")
                    font.pixelSize: 24
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }

                Image {
                    width: 48
                    height: 48
                    source: root.imageSource(card.peakRankIconPath)
                    fillMode: Image.PreserveAspectFit
                    visible: source != ""
                }

                Text {
                    width: 58
                    height: 48
                    text: card.peakRankText || "N/A"
                    color: root.value("muted")
                    font.pixelSize: 12
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    wrapMode: Text.Wrap
                    visible: !card.peakRankIconPath
                }
            }

            Column {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8

                Item {
                    width: 124
                    height: 124

                    Image {
                        id: currentRankImage
                        anchors.fill: parent
                        source: root.imageSource(card.rankIconPath)
                        fillMode: Image.PreserveAspectFit
                        visible: status === Image.Ready
                    }

                    Text {
                        anchors.centerIn: parent
                        width: parent.width - 10
                        text: card.rankText || "N/A"
                        color: root.value("muted")
                        font.pixelSize: 14
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        wrapMode: Text.Wrap
                        visible: currentRankImage.status !== Image.Ready
                    }
                }

                Rectangle {
                    width: 108
                    height: 7
                    radius: 3
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: root.alphaColor(root.value("cardAlt"), 0.88)
                    clip: true

                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: parent.width * Math.max(0, Math.min(Number(card.rrProgress || 0), 100)) / 100
                        radius: 3
                        color: root.value("accent")
                    }

                    ToolTip.visible: rrMouse.containsMouse
                    ToolTip.text: card.rrText || "RR N/A"
                    ToolTip.delay: 450

                    MouseArea {
                        id: rrMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        acceptedButtons: Qt.NoButton
                    }
                }
            }
        }
    }

    component StatChip: Rectangle {
        id: statRoot
        property string label: ""
        property string textValue: "N/A"
        property string tone: "neutral"
        property var theme: ({})

        Layout.preferredWidth: 58
        Layout.preferredHeight: 40
        radius: 10
        color: alphaColor(value("panel"), 0.72)
        border.color: alphaColor(value("borderSoft"), 0.88)

        function value(key) {
            return theme && theme[key] ? theme[key] : "transparent"
        }

        function alphaColor(color, alpha) {
            var parsed = Qt.color(color || value("card"))
            return Qt.rgba(parsed.r, parsed.g, parsed.b, alpha)
        }

        Column {
            anchors.centerIn: parent
            spacing: 1

            Text {
                width: 48
                text: label
                color: statRoot.value("muted")
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }

            Text {
                width: 48
                text: textValue
                color: root.statColor(tone, textValue)
                font.pixelSize: 13
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }
        }
    }

    component PlayerActionButton: Rectangle {
        id: buttonRoot
        property string iconPath: ""
        property string fallbackText: ""
        property string tooltipText: ""
        property var theme: ({})
        signal clicked()

        Layout.preferredWidth: 18
        Layout.preferredHeight: 18
        radius: 4
        color: buttonMouse.containsMouse ? alphaColor(value("accentHover"), 0.22) : "transparent"
        border.color: buttonMouse.containsMouse ? value("accentHover") : "transparent"

        function value(key) {
            return theme && theme[key] ? theme[key] : "transparent"
        }

        function imageSource(path) {
            if (!path) {
                return ""
            }
            var normalized = String(path).replace(/\\/g, "/")
            if (normalized.indexOf("file:/") === 0 || normalized.indexOf("qrc:/") === 0) {
                return normalized
            }
            return "file:///" + normalized
        }

        function alphaColor(color, alpha) {
            var parsed = Qt.color(color || value("card"))
            return Qt.rgba(parsed.r, parsed.g, parsed.b, alpha)
        }

        Image {
            id: actionIcon
            anchors.fill: parent
            anchors.margins: 1
            source: buttonRoot.imageSource(iconPath)
            fillMode: Image.PreserveAspectFit
            opacity: buttonMouse.containsMouse ? 1.0 : 0.86
            visible: status === Image.Ready
        }

        Text {
            anchors.centerIn: parent
            text: fallbackText
            color: buttonMouse.containsMouse ? buttonRoot.value("accentHover") : buttonRoot.value("text")
            font.pixelSize: 11
            font.bold: true
            visible: actionIcon.status !== Image.Ready
        }

        MouseArea {
            id: buttonMouse
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: buttonRoot.clicked()
        }

        ToolTip.visible: buttonMouse.containsMouse && tooltipText.length > 0
        ToolTip.text: tooltipText
        ToolTip.delay: 450
    }
}
