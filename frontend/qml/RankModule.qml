import QtQuick
import QtQuick.Controls

Rectangle {
    id: root

    property var card: ({})
    property var theme: ({})

    radius: 14
    color: alphaColor(value("panel"), 0.58)
    border.color: alphaColor(value("borderSoft"), 0.86)
    border.width: 1
    antialiasing: true

    function value(key) {
        return theme && theme[key] ? theme[key] : "transparent"
    }

    function alphaColor(color, alpha) {
        var parsed = Qt.color(color || value("card"))
        return Qt.rgba(parsed.r, parsed.g, parsed.b, alpha)
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

    function clamp(valueToClamp, minimum, maximum) {
        return Math.max(minimum, Math.min(Number(valueToClamp || 0), maximum))
    }

    function recentModel() {
        var source = card.ratingChanges || []
        if (!source.length) {
            return []
        }
        var result = []
        for (var i = 0; i < 3; i++) {
            var item = source[i] || { "valueText": "0", "numericValue": 0, "tone": "neutral" }
            result.push(item)
        }
        return result
    }

    function toneFor(change) {
        if ((change.tone || "") === "positive" || Number(change.numericValue || 0) > 0) {
            return "positive"
        }
        if ((change.tone || "") === "negative" || Number(change.numericValue || 0) < 0) {
            return "negative"
        }
        return "neutral"
    }

    function toneColor(change) {
        var tone = toneFor(change)
        if (tone === "positive") {
            return value("teal")
        }
        if (tone === "negative") {
            return value("red")
        }
        return value("muted")
    }

    function rrValueText() {
        var text = String(card.rrText || "").trim()
        text = text.replace(/\s*RR\s*$/i, "").trim()
        if (!text.length || text.toUpperCase().indexOf("N/A") >= 0) {
            return "0"
        }
        return text.length ? text : "0"
    }

    function rankLooksUnknown() {
        var rank = String(card.rankText || "").toLowerCase()
        return rank.length === 0 || rank === "n/a" || rank.indexOf("unknown") >= 0 || rank.indexOf("?") >= 0
    }

    Item {
        id: content
        anchors.fill: parent
        anchors.margins: 9

        Item {
            id: leftPane
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: divider.left
            anchors.rightMargin: 10

            Row {
                id: recentRow
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.topMargin: 5
                spacing: 7

                Repeater {
                    model: root.recentModel()

                    Rectangle {
                        width: 34
                        height: 34
                        radius: 17
                        color: root.alphaColor(root.toneColor(modelData), root.toneFor(modelData) === "neutral" ? 0.12 : 0.18)
                        border.color: root.alphaColor(root.toneColor(modelData), root.toneFor(modelData) === "neutral" ? 0.34 : 0.58)
                        border.width: 1
                        antialiasing: true

                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 4
                            text: modelData.valueText || modelData.text || "0"
                            color: root.toneFor(modelData) === "neutral" ? root.alphaColor(root.value("text"), 0.82) : root.toneColor(modelData)
                            font.pixelSize: 14
                            font.bold: true
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideRight
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

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.topMargin: 54
                height: 1
                color: root.alphaColor(root.value("borderSoft"), 0.58)
            }

            Row {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 8
                height: 34
                spacing: 8

                Item {
                    width: 28
                    height: 28
                    anchors.verticalCenter: parent.verticalCenter

                    Image {
                        id: peakRankImage
                        anchors.fill: parent
                        source: root.imageSource(card.peakRankIconPath)
                        fillMode: Image.PreserveAspectFit
                        opacity: 0.82
                        visible: status === Image.Ready
                    }

                    Rectangle {
                        anchors.centerIn: parent
                        width: 18
                        height: 18
                        radius: 4
                        rotation: 45
                        color: root.alphaColor(root.value("muted"), 0.12)
                        border.color: root.alphaColor(root.value("muted"), 0.38)
                        visible: peakRankImage.status !== Image.Ready
                    }
                }

                Text {
                    width: parent.width - 36
                    anchors.verticalCenter: parent.verticalCenter
                    text: card.peakActText || "N/A"
                    color: root.alphaColor(root.value("text"), 0.78)
                    font.pixelSize: 25
                    font.bold: false
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                }
            }
        }

        Rectangle {
            id: divider
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.right: rightPane.left
            anchors.rightMargin: 10
            width: 1
            color: root.alphaColor(root.value("borderSoft"), 0.62)
        }

        Item {
            id: rightPane
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            width: Math.min(118, Math.max(104, parent.width * 0.42))

            Item {
                id: rankIconSlot
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: 2
                width: 78
                height: 78

                Image {
                    id: currentRankImage
                    anchors.fill: parent
                    source: root.imageSource(card.rankIconPath)
                    fillMode: Image.PreserveAspectFit
                    opacity: root.rankLooksUnknown() ? 0.58 : 0.92
                    visible: status === Image.Ready
                }

                Text {
                    anchors.centerIn: parent
                    width: parent.width - 8
                    text: card.rankText || "N/A"
                    color: root.alphaColor(root.value("muted"), 0.82)
                    font.pixelSize: 13
                    font.bold: true
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.Wrap
                    visible: currentRankImage.status !== Image.Ready
                }
            }

            Rectangle {
                id: rrProgressBar
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: rankIconSlot.bottom
                anchors.topMargin: 7
                height: 9
                radius: 5
                color: root.alphaColor(root.value("muted"), 0.18)
                clip: true

                Rectangle {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: parent.width * root.clamp(card.rrProgress, 0, 100) / 100
                    radius: 5
                    color: root.value("accent") !== "transparent" ? root.value("accent") : root.value("cyan")
                    opacity: 0.88
                }

                ToolTip.visible: rrMouse.containsMouse
                ToolTip.text: root.rrValueText() + " / 100 RR"
                ToolTip.delay: 450

                MouseArea {
                    id: rrMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.NoButton
                }
            }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: rrProgressBar.bottom
                anchors.topMargin: 7
                spacing: 5

                Text {
                    text: root.rrValueText()
                    color: root.value("cyan") !== "transparent" ? root.value("cyan") : root.value("accent")
                    font.pixelSize: 20
                    font.bold: true
                }

                Text {
                    text: "/ 100 RR"
                    color: root.alphaColor(root.value("muted"), 0.9)
                    font.pixelSize: 18
                    font.bold: false
                }
            }
        }
    }
}
