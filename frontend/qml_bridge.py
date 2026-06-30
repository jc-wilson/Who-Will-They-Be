from PySide6.QtCore import QObject, Property, Signal, Slot


class QmlProbeBridge(QObject):
    dataChanged = Signal()
    refreshRequested = Signal()

    def __init__(self, window_state, parent=None):
        super().__init__(parent)
        self._window_state = window_state

    @Property(str, notify=dataChanged)
    def appTitle(self):
        return "ValScanner"

    @Property(str, notify=dataChanged)
    def currentThemeName(self):
        return str(getattr(self._window_state, "current_theme_name", "") or "")

    @Property(int, notify=dataChanged)
    def leftPlayerCount(self):
        return len(getattr(self._window_state, "left_players", []) or [])

    @Property(int, notify=dataChanged)
    def rightPlayerCount(self):
        return len(getattr(self._window_state, "right_players", []) or [])

    @Slot()
    def requestRefresh(self):
        self.refreshRequested.emit()

    def notify_bindings(self):
        self.dataChanged.emit()
