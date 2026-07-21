import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    height: 96
    color: root.colorValue("window", root.colorValue("main", "#111823"))

    property var theme: topBarBridge.theme
    property int controlHeight: 50

    Image {
        anchors.fill: parent
        source: topBarBridge.backgroundPath
        fillMode: Image.Stretch
        smooth: true
        visible: status === Image.Ready
    }

    function colorValue(name, fallback) {
        return theme && theme[name] ? theme[name] : fallback
    }

    function compactStartingSideText() {
        var sideText = String(topBarBridge.startingSideText || "").trim()
        return sideText.replace(/^starting\s*side\s*:?\s*/i, "")
    }

    function titleCaseText(value) {
        var words = String(value || "").trim().toLowerCase().split(/\s+/)
        for (var index = 0; index < words.length; index += 1) {
            if (words[index].length > 0) {
                words[index] = words[index].charAt(0).toUpperCase() + words[index].slice(1)
            }
        }
        return words.join(" ")
    }

    function startingSideDisplayText() {
        return titleCaseText(compactStartingSideText())
    }

    function itemRectInRoot(item) {
        var point = item.mapToItem(root, 0, 0)
        return {
            "x": point.x,
            "y": point.y,
            "width": item.width,
            "height": item.height
        }
    }

    component TopBarButton: Rectangle {
        id: button
        property string text: ""
        property bool accent: false
        property bool danger: false
        property bool blue: false
        property bool controlEnabled: true
        property int textPixelSize: 14
        property int buttonHeight: root.controlHeight
        property string iconSource: ""
        property bool lockIcon: false
        property bool exitDoorIcon: false
        property bool spannerIcon: false
        signal clicked()

        Layout.minimumHeight: button.buttonHeight
        Layout.preferredHeight: button.buttonHeight
        Layout.minimumWidth: Math.max(
            46,
            buttonText.implicitWidth + 34 + ((button.iconSource.length > 0 || button.lockIcon || button.exitDoorIcon || button.spannerIcon) ? 18 : 0)
        )
        Layout.preferredWidth: Math.max(
            46,
            buttonText.implicitWidth + 34 + ((button.iconSource.length > 0 || button.lockIcon || button.exitDoorIcon || button.spannerIcon) ? 18 : 0)
        )
        radius: 6
        opacity: controlEnabled ? 1.0 : 0.55
        color: {
            if (!controlEnabled) {
                return root.colorValue("borderSoft", "transparent")
            }
            if (danger) {
                return buttonMouse.pressed ? root.colorValue("redPressed", "transparent")
                    : buttonMouse.containsMouse ? root.colorValue("redHover", "transparent")
                    : root.colorValue("red", "transparent")
            }
            if (blue) {
                return buttonMouse.pressed ? "#1f54cc"
                    : buttonMouse.containsMouse ? "#3578ff"
                    : "#2867e8"
            }
            if (accent) {
                return buttonMouse.pressed ? root.colorValue("accentPressed", "transparent")
                    : buttonMouse.containsMouse ? root.colorValue("accentHover", "transparent")
                    : root.colorValue("accent", "transparent")
            }
            return buttonMouse.containsMouse ? root.colorValue("cardAlt", "transparent")
                : root.colorValue("card", "transparent")
        }
        border.color: danger ? "#ff8c98"
            : blue ? "#6fa0ff"
            : accent ? "transparent"
            : root.colorValue("borderSoft", "transparent")
        border.width: danger || blue ? 1 : (accent ? 0 : 1)

        Behavior on color {
            ColorAnimation { duration: 120; easing.type: Easing.OutCubic }
        }

        Row {
            anchors.centerIn: parent
            spacing: (button.iconSource.length > 0 || button.lockIcon || button.exitDoorIcon || button.spannerIcon) ? 8 : 0

            Item {
                width: (button.iconSource.length > 0 || button.lockIcon || button.exitDoorIcon || button.spannerIcon) ? 16 : 0
                height: 16
                anchors.verticalCenter: parent.verticalCenter
                visible: button.iconSource.length > 0 || button.lockIcon || button.exitDoorIcon || button.spannerIcon

                Image {
                    id: assetIcon
                    anchors.centerIn: parent
                    width: 16
                    height: 16
                    source: button.iconSource
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    visible: button.iconSource.length > 0 && status === Image.Ready
                }

                Rectangle {
                    width: 10
                    height: 9
                    radius: 5
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 0
                    color: "transparent"
                    border.color: root.colorValue("text", "white")
                    border.width: 2
                    visible: button.lockIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 14
                    height: 10
                    radius: 2
                    anchors.horizontalCenter: parent.horizontalCenter
                    y: 6
                    color: root.colorValue("text", "white")
                    visible: button.lockIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 11
                    height: 14
                    radius: 1
                    x: 1
                    y: 1
                    color: "transparent"
                    border.color: root.colorValue("text", "white")
                    border.width: 2
                    visible: button.exitDoorIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 6
                    height: 2
                    x: 9
                    y: 7
                    radius: 1
                    color: root.colorValue("text", "white")
                    visible: button.exitDoorIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 6
                    height: 6
                    x: 9
                    y: 5
                    color: "transparent"
                    border.color: root.colorValue("text", "white")
                    border.width: 2
                    rotation: 45
                    visible: button.exitDoorIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 7
                    height: 7
                    radius: 4
                    x: 0
                    y: 0
                    color: "transparent"
                    border.color: root.colorValue("text", "white")
                    border.width: 2
                    visible: button.spannerIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 13
                    height: 4
                    radius: 2
                    x: 4
                    y: 8
                    color: root.colorValue("text", "white")
                    rotation: -35
                    visible: button.spannerIcon && !assetIcon.visible
                }

                Rectangle {
                    width: 5
                    height: 5
                    radius: 1
                    x: 11
                    y: 10
                    color: root.colorValue("text", "white")
                    rotation: -35
                    visible: button.spannerIcon && !assetIcon.visible
                }
            }

            Text {
                id: buttonText
                text: button.text
                color: root.colorValue("text", "white")
                font.pixelSize: button.textPixelSize
                font.bold: true
                font.weight: Font.ExtraBold
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        MouseArea {
            id: buttonMouse
            anchors.fill: parent
            enabled: button.controlEnabled
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: button.clicked()
        }
    }

    component TopBarToggle: Item {
        id: toggle
        property string label: ""
        property bool checked: false
        property bool controlEnabled: true
        signal toggled(bool checked)

        Layout.minimumWidth: labelText.implicitWidth + 65
        Layout.preferredWidth: labelText.implicitWidth + 72
        Layout.minimumHeight: root.controlHeight
        Layout.preferredHeight: root.controlHeight
        opacity: controlEnabled ? 1.0 : 0.55

        RowLayout {
            anchors.fill: parent
            spacing: 9

            Text {
                id: labelText
                text: toggle.label
                color: root.colorValue("text", "white")
                font.pixelSize: 14
                font.bold: true
                font.weight: Font.ExtraBold
                elide: Text.ElideRight
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
            }

            Rectangle {
                Layout.preferredWidth: 48
                Layout.preferredHeight: 26
                Layout.alignment: Qt.AlignVCenter
                radius: 13
                color: toggle.checked ? root.colorValue("accent", "transparent") : root.colorValue("cardAlt", "transparent")
                border.color: toggleMouse.containsMouse ? root.colorValue("accentHover", "transparent") : root.colorValue("borderSoft", "transparent")
                border.width: 1

                Rectangle {
                    width: 20
                    height: 20
                    radius: 10
                    x: toggle.checked ? parent.width - width - 3 : 3
                    anchors.verticalCenter: parent.verticalCenter
                    color: root.colorValue("text", "white")
                    border.color: root.colorValue("border", "transparent")
                    border.width: 1

                    Behavior on x {
                        NumberAnimation { duration: 150; easing.type: Easing.OutCubic }
                    }
                }

                MouseArea {
                    id: toggleMouse
                    anchors.fill: parent
                    enabled: toggle.controlEnabled
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: toggle.toggled(!toggle.checked)
                }
            }
        }
    }

    Rectangle {
        id: surface
        anchors.fill: parent
        anchors.leftMargin: 0
        anchors.rightMargin: 0
        anchors.topMargin: 0
        anchors.bottomMargin: 0
        radius: 0
        color: "transparent"
        border.color: "transparent"
        border.width: 0

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            anchors.topMargin: 18
            anchors.bottomMargin: 18
            spacing: 14

            RowLayout {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: metaContent.implicitWidth + 28
                Layout.minimumWidth: metaContent.implicitWidth + 28
                Layout.maximumWidth: metaContent.implicitWidth + 28
                spacing: 0

                RowLayout {
                    visible: false
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: 0
                    Layout.minimumWidth: 0
                    spacing: 10

                    Item {
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignVCenter

                        Image {
                            id: topBarLogo
                            anchors.centerIn: parent
                            width: 30
                            height: 30
                            source: topBarBridge.logoPath
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            visible: status === Image.Ready
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "VS"
                            color: root.colorValue("text", "white")
                            font.pixelSize: 12
                            font.weight: Font.ExtraBold
                            visible: topBarLogo.status !== Image.Ready
                        }
                    }

                    Text {
                        text: "ValScanner"
                        color: root.colorValue("text", "white")
                        font.pixelSize: 18
                        font.weight: Font.ExtraBold
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                    }
                }

                Rectangle {
                    Layout.minimumWidth: metaContent.implicitWidth + 28
                    Layout.preferredWidth: metaContent.implicitWidth + 28
                    Layout.maximumWidth: metaContent.implicitWidth + 28
                    Layout.preferredHeight: root.controlHeight
                    radius: 7
                    color: root.colorValue("card", "transparent")
                    border.color: root.colorValue("borderSoft", "transparent")
                    border.width: 1

                    RowLayout {
                        id: metaContent
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 8

                        Text {
                            text: String(topBarBridge.gamemode || "Unknown").toUpperCase()
                            color: root.colorValue("text", "white")
                            font.pixelSize: 14
                            font.weight: Font.Bold
                            elide: Text.ElideRight
                            Layout.preferredWidth: implicitWidth
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            text: "\u2022"
                            color: root.colorValue("muted", "white")
                            font.pixelSize: 11
                            font.weight: Font.ExtraBold
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            text: String(topBarBridge.server || "Unknown").toUpperCase()
                            color: root.colorValue("text", "white")
                            font.pixelSize: 14
                            font.weight: Font.Bold
                            elide: Text.ElideRight
                            Layout.preferredWidth: implicitWidth
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            text: "\u2022"
                            color: root.colorValue("muted", "white")
                            font.pixelSize: 11
                            font.weight: Font.ExtraBold
                            visible: root.startingSideDisplayText().length > 0
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            text: "\u26e8"
                            color: root.colorValue("accent", "white")
                            font.pixelSize: 14
                            font.weight: Font.Bold
                            visible: root.startingSideDisplayText().length > 0
                            Layout.alignment: Qt.AlignVCenter
                        }

                        Text {
                            text: root.startingSideDisplayText().toUpperCase()
                            color: root.colorValue("accent", "white")
                            font.pixelSize: 14
                            font.weight: Font.ExtraBold
                            elide: Text.ElideRight
                            visible: text.length > 0
                            Layout.preferredWidth: implicitWidth
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }
                }
            }

            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                Layout.minimumWidth: 670
                Layout.preferredWidth: 690
                Layout.maximumWidth: 720
                Layout.preferredHeight: root.controlHeight
                radius: 7
                color: root.colorValue("card", "transparent")
                border.color: root.colorValue("borderSoft", "transparent")
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    anchors.topMargin: 0
                    anchors.bottomMargin: 0
                    spacing: 12

                    Item {
                        Layout.preferredWidth: 42
                        Layout.preferredHeight: 42
                        Layout.alignment: Qt.AlignVCenter

                        Image {
                            id: selectedAgentIcon
                            anchors.centerIn: parent
                            width: 42
                            height: 42
                            source: topBarBridge.selectedAgentIconPath
                            fillMode: Image.PreserveAspectCrop
                            smooth: true
                            visible: status === Image.Ready
                        }

                        Rectangle {
                            anchors.centerIn: parent
                            width: 42
                            height: 42
                            radius: 5
                            color: root.colorValue("cardAlt", "transparent")
                            border.color: root.colorValue("borderSoft", "transparent")
                            border.width: 1
                            visible: selectedAgentIcon.status !== Image.Ready

                            Text {
                                anchors.centerIn: parent
                                text: String(topBarBridge.selectedAgent || "?").charAt(0).toUpperCase()
                                color: root.colorValue("text", "white")
                                font.pixelSize: 14
                                font.bold: true
                                font.weight: Font.ExtraBold
                            }
                        }
                    }

                    Item {
                        Layout.minimumWidth: agentNameText.implicitWidth + 22
                        Layout.preferredWidth: agentNameText.implicitWidth + 26
                        Layout.minimumHeight: root.controlHeight
                        Layout.preferredHeight: root.controlHeight

                        RowLayout {
                            anchors.fill: parent
                            spacing: 5

                            Text {
                                id: agentNameText
                                text: topBarBridge.selectedAgent
                                color: root.colorValue("text", "white")
                                font.pixelSize: 15
                                font.bold: true
                                font.weight: Font.ExtraBold
                                elide: Text.ElideRight
                                Layout.alignment: Qt.AlignVCenter
                            }

                            Image {
                                source: topBarBridge.chevronDownIconPath
                                Layout.preferredWidth: 10
                                Layout.preferredHeight: 10
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                                Layout.alignment: Qt.AlignVCenter
                            }
                        }

                        MouseArea {
                            id: agentMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: topBarBridge.openAgentSelector()
                        }
                    }

                    TopBarButton {
                        text: "Lock Agent"
                        blue: true
                        iconSource: topBarBridge.lockIconPath
                        lockIcon: true
                        controlEnabled: topBarBridge.lockEnabled
                        buttonHeight: 44
                        Layout.minimumWidth: 118
                        Layout.preferredWidth: 126
                        onClicked: topBarBridge.lockAgent()
                    }

                    TopBarToggle {
                        label: "Auto-Lock"
                        checked: topBarBridge.autoLockEnabled
                        onToggled: function(nextChecked) { topBarBridge.setAutoLockEnabled(nextChecked) }
                    }

                    TopBarToggle {
                        label: "Map Specific"
                        checked: topBarBridge.mapSpecificEnabled
                        controlEnabled: topBarBridge.mapSpecificAvailable
                        onToggled: function(nextChecked) { topBarBridge.setMapSpecificEnabled(nextChecked) }
                    }
                }
            }

            RowLayout {
                Layout.alignment: Qt.AlignVCenter
                Layout.fillWidth: true
                spacing: 9

                Item {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 0
                }

                TopBarButton {
                    text: "Dodge Game"
                    danger: true
                    iconSource: topBarBridge.dodgeIconPath
                    exitDoorIcon: true
                    controlEnabled: topBarBridge.dodgeEnabled
                    onClicked: topBarBridge.dodgeGame()
                }

                TopBarButton {
                    text: "Load More Games"
                    iconSource: topBarBridge.loadMoreIconPath
                    controlEnabled: topBarBridge.loadMoreEnabled
                    onClicked: topBarBridge.loadMoreGames()
                }

                TopBarButton {
                    text: "Loadouts"
                    iconSource: topBarBridge.loadoutsIconPath
                    onClicked: topBarBridge.openLoadouts()
                }

                TopBarButton {
                    id: toolsButton
                    text: "Tools"
                    iconSource: topBarBridge.toolsIconPath
                    spannerIcon: true
                    onClicked: topBarBridge.openToolsAt(root.itemRectInRoot(toolsButton))
                }

                TopBarButton {
                    text: "Refresh"
                    iconSource: topBarBridge.refreshIconPath
                    controlEnabled: topBarBridge.refreshEnabled
                    onClicked: topBarBridge.refresh()
                }

                Rectangle {
                    visible: topBarBridge.appearOfflineVisible
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: visible ? 52 : 0
                    Layout.preferredHeight: root.controlHeight
                    radius: 6
                    color: root.colorValue("card", "transparent")
                    border.color: root.colorValue("borderSoft", "transparent")
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: "OFF"
                        color: root.colorValue("muted", "white")
                        font.pixelSize: 12
                        font.bold: true
                        font.weight: Font.ExtraBold
                    }
                }
            }
        }
    }
}
