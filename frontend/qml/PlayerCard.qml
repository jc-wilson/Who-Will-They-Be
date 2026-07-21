import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root

    property var card: ({})
    property var theme: ({})
    readonly property int statBandWidth: 338
    readonly property real statChipWidth: (statBandWidth - 4 * 5) / 5
    readonly property int rightPanelVerticalInset: 0
    readonly property int solidCircleVisualTopOffset: 6
    readonly property int bottomVisualOffset: 4
    readonly property int nameRowEdgePadding: 8
    signal openTracker(string trackerUrl)
    signal openVtl(string vtlUrl)
    signal copyName(string clipboardName)
    signal openLoadout(string playerKey)
    signal toggleFlag(string puuid)

    implicitHeight: 156
    height: 156
    radius: 6
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

    function isAgentPlaceholder() {
        return String(card.agentName || "").trim().toUpperCase() === "N/A"
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
        anchors.rightMargin: 12
        anchors.topMargin: 12
        anchors.bottomMargin: 12
        spacing: 12

        Item {
            Layout.preferredWidth: 132
            Layout.preferredHeight: 132

            Item {
                anchors.fill: parent
                clip: true

                Image {
                    id: agentPortrait
                    anchors.fill: parent
                    source: root.imageSource(card.agentIconPath)
                    fillMode: Image.PreserveAspectFit
                    visible: status === Image.Ready
                }

                BreathingDotsIndicator {
                    anchors.centerIn: parent
                    color: root.value("muted")
                    visible: agentPortrait.status !== Image.Ready && root.isAgentPlaceholder()
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
                    visible: agentPortrait.status !== Image.Ready && !root.isAgentPlaceholder()
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                width: Math.max(30, levelText.implicitWidth + 8)
                height: 22
                radius: 3
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

        SectionDivider {}

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.minimumWidth: 260

                ColumnLayout {
                    width: root.statBandWidth
                    height: 132
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 11

                    RowLayout {
                        Layout.preferredWidth: root.statBandWidth
                        Layout.preferredHeight: 22
                        spacing: 8

                        Item {
                            id: nameIdentityGroup
                            readonly property int maxWidth: 252
                            readonly property int iconSpacing: nameIdentityIcons.width > 0 ? 4 : 0

                            Layout.alignment: Qt.AlignTop
                            Layout.preferredWidth: Math.min(nameText.implicitWidth + nameIdentityIcons.width + iconSpacing, maxWidth)
                            Layout.preferredHeight: 22

                            Text {
                                id: nameText
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: Math.max(0, parent.width - nameIdentityIcons.width - nameIdentityGroup.iconSpacing)
                                text: card.displayName || "Unknown"
                                color: nameMouse.containsMouse ? root.value("cyan") : root.value("text")
                                font.pixelSize: 20
                                font.bold: true
                                elide: Text.ElideRight

                                MouseArea {
                                    id: nameMouse
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: root.openTracker(card.trackerUrl || "")
                                }
                            }

                            RowLayout {
                                id: nameIdentityIcons
                                anchors.left: nameText.right
                                anchors.leftMargin: nameIdentityGroup.iconSpacing
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 4

                                NameRowIcon {
                                    iconPath: card.hasBuddyEquipped ? (card.buddyIconPath || "") : ""
                                    tooltipText: "Riot gun buddy"
                                    theme: root.theme
                                    Layout.alignment: Qt.AlignTop
                                }

                                NameRowIcon {
                                    iconPath: card.playerIconPath || ""
                                    tooltipText: card.playerIconTooltip || "Player icon"
                                    theme: root.theme
                                    Layout.alignment: Qt.AlignTop
                                }
                            }
                        }

                        Item { Layout.fillWidth: true }

                        PlayerActionButton {
                            iconPath: card.copyIconPath || ""
                            fallbackText: "C"
                            tooltipText: "Copy " + (card.clipboardName || "")
                            theme: root.theme
                            Layout.alignment: Qt.AlignTop
                            onClicked: root.copyName(card.clipboardName || "")
                        }

                        PlayerActionButton {
                            iconPath: card.vtlIconPath || ""
                            fallbackText: "V"
                            tooltipText: "View on VTL.lol"
                            theme: root.theme
                            Layout.alignment: Qt.AlignTop
                            onClicked: root.openVtl(card.vtlUrl || "")
                        }

                        PlayerActionButton {
                            iconPath: card.flagIconPath || ""
                            fallbackText: "F"
                            tooltipText: card.flagTooltip || "Toggle flagged player"
                            theme: root.theme
                            Layout.alignment: Qt.AlignTop
                            Layout.rightMargin: root.nameRowEdgePadding
                            onClicked: root.toggleFlag(card.puuid || "")
                        }
                    }

                RowLayout {
                    Layout.preferredWidth: root.statBandWidth
                    Layout.preferredHeight: 48
                    spacing: 12

                    Rectangle {
                        id: weaponStrip
                        Layout.preferredWidth: root.statBandWidth
                        Layout.preferredHeight: 44
                        radius: 5
                        color: weaponMouse.containsMouse ? root.alphaColor(root.value("accentHover"), 0.16) : root.alphaColor(root.value("panel"), 0.72)
                        border.color: weaponMouse.containsMouse ? root.value("accentHover") : root.alphaColor(root.value("borderSoft"), 0.82)

                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 7
                            spacing: 8

                            Repeater {
                                model: card.weaponIcons || []

                                Item {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true

                                    Image {
                                        anchors.fill: parent
                                        anchors.margins: 2
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
                        text: card.partyGroupId ? "Party " + card.partyGroupId : ""
                        color: root.value("accentHover")
                        font.pixelSize: 11
                        font.bold: true
                        visible: card.partyGroupId
                    }
                }

                RowLayout {
                    Layout.preferredWidth: root.statBandWidth
                    spacing: 5

                    StatChip { label: "GAMES"; textValue: card.gamesText || "0"; tone: "neutral"; theme: root.theme }
                    StatChip { label: "W/L"; textValue: card.winRateText || "N/A"; tone: card.winRateTone || "neutral"; theme: root.theme }
                    StatChip { label: "ACS"; textValue: card.acsText || "N/A"; tone: card.acsTone || "neutral"; theme: root.theme }
                    StatChip { label: "KD"; textValue: card.kdText || "N/A"; tone: card.kdTone || "neutral"; theme: root.theme }
                    StatChip { label: "HS"; textValue: card.hsText || "N/A"; tone: card.hsTone || "neutral"; theme: root.theme }
                }
            }
        }

        SectionDivider {}

        Item {
            Layout.preferredWidth: 300
            Layout.fillHeight: true

            Row {
                id: recentRow
                anchors.right: currentRankColumn.left
                anchors.rightMargin: 28
                anchors.top: parent.top
                anchors.topMargin: root.rightPanelVerticalInset + root.solidCircleVisualTopOffset
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

            Item {
                width: recentRow.width
                height: 40
                anchors.right: currentRankColumn.left
                anchors.rightMargin: 28
                anchors.bottom: parent.bottom
                anchors.bottomMargin: root.rightPanelVerticalInset + root.bottomVisualOffset

                Item {
                    id: peakRankSlot
                    width: 42
                    height: 40
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter

                    Image {
                        width: 40
                        height: 40
                        anchors.centerIn: parent
                        source: root.imageSource(card.peakRankIconPath)
                        fillMode: Image.PreserveAspectFit
                        visible: source != ""
                    }

                    Text {
                        anchors.fill: parent
                        text: card.peakRankText || "N/A"
                        color: root.value("muted")
                        font.pixelSize: 11
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.Wrap
                        visible: !card.peakRankIconPath
                    }
                }

                Text {
                    anchors.left: peakRankSlot.right
                    anchors.leftMargin: 4
                    anchors.verticalCenter: parent.verticalCenter
                    width: Math.max(44, implicitWidth + 10)
                    height: 40
                    text: card.peakActText || "N/A"
                    color: root.value("muted")
                    font.pixelSize: 24
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    elide: Text.ElideRight
                }
            }

            Item {
                id: currentRankColumn
                width: 108
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom

                Item {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.top: parent.top
                    anchors.topMargin: root.solidCircleVisualTopOffset
                    width: 114
                    height: 114

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
                    id: currentRrBar
                    width: 108
                    height: 7
                    radius: 3
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: root.solidCircleVisualTopOffset
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
                        cursorShape: Qt.PointingHandCursor
                        acceptedButtons: Qt.NoButton
                    }
                }
            }
        }
    }

    component NameRowIcon: Rectangle {
        id: iconRoot
        property string iconPath: ""
        property string tooltipText: ""
        property var theme: ({})

        visible: iconPath.length > 0
        Layout.preferredWidth: visible ? 20 : 0
        Layout.preferredHeight: 20
        radius: 3
        color: "transparent"
        border.color: "transparent"

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

        Image {
            id: nameIcon
            anchors.fill: parent
            source: iconRoot.imageSource(iconPath)
            fillMode: Image.PreserveAspectFit
            visible: status === Image.Ready
        }

        MouseArea {
            id: nameIconMouse
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.NoButton
        }

        ToolTip.visible: nameIconMouse.containsMouse && tooltipText.length > 0
        ToolTip.text: tooltipText
        ToolTip.delay: 450
    }

    component SectionDivider: Rectangle {
        Layout.preferredWidth: 1
        Layout.fillHeight: true
        Layout.topMargin: 8
        Layout.bottomMargin: 8
        color: root.alphaColor(root.value("borderSoft"), 0.45)
    }

    component BreathingDotsIndicator: Item {
        id: dotsRoot
        property color color: root.value("muted")

        width: 44
        height: 18

        Row {
            anchors.centerIn: parent
            spacing: 6

            Repeater {
                model: 3

                Rectangle {
                    id: dot
                    property int dotIndex: index

                    width: 8
                    height: 8
                    radius: 4
                    color: dotsRoot.color
                    opacity: 0.42

                    transform: Scale {
                        id: dotScale
                        origin.x: dot.width / 2
                        origin.y: dot.height / 2
                        xScale: 0.72
                        yScale: 0.72
                    }

                    SequentialAnimation {
                        running: dotsRoot.visible
                        loops: Animation.Infinite
                        PauseAnimation { duration: dot.dotIndex * 170 }
                        ParallelAnimation {
                            NumberAnimation { target: dotScale; properties: "xScale,yScale"; to: 1.18; duration: 520; easing.type: Easing.InOutSine }
                            NumberAnimation { target: dot; property: "opacity"; to: 1.0; duration: 520; easing.type: Easing.InOutSine }
                        }
                        ParallelAnimation {
                            NumberAnimation { target: dotScale; properties: "xScale,yScale"; to: 0.72; duration: 520; easing.type: Easing.InOutSine }
                            NumberAnimation { target: dot; property: "opacity"; to: 0.42; duration: 520; easing.type: Easing.InOutSine }
                        }
                        PauseAnimation { duration: (2 - dot.dotIndex) * 170 }
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

        Layout.preferredWidth: root.statChipWidth
        Layout.preferredHeight: 40
        radius: 5
        color: "transparent"
        border.color: "transparent"
        border.width: 0

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
                width: statRoot.width
                text: label
                color: statRoot.value("muted")
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
                elide: Text.ElideRight
            }

            Text {
                width: statRoot.width
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

        Layout.preferredWidth: 20
        Layout.preferredHeight: 20
        radius: 3
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
            source: buttonRoot.imageSource(iconPath)
            fillMode: Image.PreserveAspectFit
            opacity: buttonMouse.containsMouse ? 1.0 : 0.86
            visible: status === Image.Ready
        }

        Text {
            anchors.centerIn: parent
            text: fallbackText
            color: buttonMouse.containsMouse ? buttonRoot.value("accentHover") : buttonRoot.value("text")
            font.pixelSize: 13
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
