import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    radius: 12
    color: "#121820"
    border.color: "#2f3b4d"
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        Text {
            text: "ValScanner QML Probe"
            color: "#f2f7ff"
            font.pixelSize: 18
            font.bold: true
            Layout.fillWidth: true
        }

        Text {
            text: "Theme: " + bridge.currentThemeName
            color: "#b8c7d9"
            font.pixelSize: 13
            Layout.fillWidth: true
        }

        Text {
            text: "Left: " + bridge.leftPlayerCount + " | Right: " + bridge.rightPlayerCount
            color: "#b8c7d9"
            font.pixelSize: 13
            Layout.fillWidth: true
        }

        Button {
            text: "Refresh"
            Layout.alignment: Qt.AlignLeft
            onClicked: bridge.requestRefresh()
        }
    }
}
