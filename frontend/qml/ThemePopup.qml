import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    width: 840
    height: 640
    radius: 22
    color: bridge.styleColors.main || "#111823"
    border.color: bridge.styleColors.borderSoft || "#27384d"
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 30
        spacing: 18

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 38

            Text {
                anchors.centerIn: parent
                text: "Themes"
                color: bridge.styleColors.text || "#eef4ff"
                font.pixelSize: 24
                font.bold: true
            }

            RowLayout {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                spacing: 10

                Text {
                    text: "Opaque"
                    color: bridge.styleColors.muted || "#93a4bb"
                    font.pixelSize: 12
                    font.bold: true
                    Layout.alignment: Qt.AlignVCenter
                }

                Item {
                    id: surfaceToggle
                    property bool checked: bridge.opaqueSurface
                    Layout.preferredWidth: 58
                    Layout.preferredHeight: 30
                    Layout.alignment: Qt.AlignVCenter

                    Rectangle {
                        id: toggleTrack
                        anchors.fill: parent
                        radius: height / 2
                        color: surfaceToggle.checked
                            ? (bridge.styleColors.accent || "#4da3ff")
                            : (bridge.styleColors.borderSoft || "#203043")
                        border.color: surfaceToggleMouse.containsMouse
                            ? (bridge.styleColors.accentHover || bridge.styleColors.accent || "#6ab4ff")
                            : (bridge.styleColors.border || "#27384d")
                        border.width: 1

                        Behavior on color {
                            ColorAnimation { duration: 160; easing.type: Easing.OutCubic }
                        }
                        Rectangle {
                            id: toggleKnob
                            width: 24
                            height: 24
                            radius: 12
                            x: surfaceToggle.checked ? parent.width - width - 3 : 3
                            anchors.verticalCenter: parent.verticalCenter
                            color: bridge.styleColors.text || "#eef4ff"
                            border.color: "#33000000"
                            border.width: 1

                            Behavior on x {
                                NumberAnimation { duration: 170; easing.type: Easing.OutCubic }
                            }
                        }
                    }

                    MouseArea {
                        id: surfaceToggleMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: bridge.setSurfaceMode(surfaceToggle.checked ? "transparent" : "opaque")
                    }
                }
            }

            Rectangle {
                id: closeControl
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                width: 32
                height: 32
                radius: 16
                color: closeMouse.containsMouse ? (bridge.styleColors.cardAlt || "transparent") : "transparent"

                Image {
                    anchors.centerIn: parent
                    width: 16
                    height: 16
                    source: bridge.closeIconPath
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }

                Behavior on color {
                    ColorAnimation { duration: 140; easing.type: Easing.OutCubic }
                }

                MouseArea {
                    id: closeMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bridge.closePopup()
                }
            }
        }

        GridLayout {
            id: themeGrid
            Layout.alignment: Qt.AlignHCenter
            columns: 3
            columnSpacing: 16
            rowSpacing: 16

            Repeater {
                model: bridge.themeOptions

                Rectangle {
                    id: themeCard
                    property bool hovered: cardMouse.containsMouse
                    Layout.preferredWidth: 242
                    Layout.preferredHeight: 154
                    radius: 16
                    color: hovered ? modelData.cardAlt : modelData.card
                    border.color: modelData.selected ? modelData.accent : modelData.borderSoft
                    border.width: modelData.selected ? 3 : 1

                    Behavior on color {
                        ColorAnimation { duration: 150; easing.type: Easing.OutCubic }
                    }
                    MouseArea {
                        id: cardMouse
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        hoverEnabled: true
                        onClicked: bridge.selectTheme(modelData.name)
                    }

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 18
                        spacing: 8

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 54
                            radius: 12
                            color: modelData.panel
                            border.color: modelData.border
                            border.width: 1

                            Rectangle {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.bottom: parent.bottom
                                anchors.leftMargin: 10
                                anchors.rightMargin: 10
                                anchors.bottomMargin: 10
                                height: 5
                                radius: 2
                                color: modelData.accent
                            }

                            Rectangle {
                                width: 28
                                height: 28
                                radius: 14
                                anchors.right: parent.right
                                anchors.top: parent.top
                                anchors.rightMargin: 10
                                anchors.topMargin: 10
                                color: modelData.main
                                border.color: modelData.accentHover
                                border.width: 1
                            }
                        }

                        Text {
                            text: modelData.label
                            color: modelData.text
                            font.pixelSize: 17
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        Text {
                            text: modelData.selected ? "Selected" : modelData.name
                            color: modelData.muted
                            font.pixelSize: 12
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }
}
