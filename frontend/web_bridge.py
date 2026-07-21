import json

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication


class WebFrontendBridge(QObject):
    snapshotChanged = Signal(str)

    def __init__(
        self,
        snapshot_factory,
        *,
        refresh_callback=None,
        loadout_callback=None,
        flag_callback=None,
        dispatch_callback=None,
        parent=None,
    ):
        super().__init__(parent)
        self._snapshot_factory = snapshot_factory
        self._refresh_callback = refresh_callback or (lambda: None)
        self._loadout_callback = loadout_callback or (lambda _player_key: None)
        self._flag_callback = flag_callback or (lambda _puuid: None)
        self._dispatch_callback = dispatch_callback
        self._snapshot_json = "{}"
        self.refresh_snapshot(emit_signal=False)

    @Property(str, notify=snapshotChanged)
    def snapshotJson(self):
        return self._snapshot_json

    @Slot(result=str)
    def getSnapshot(self):
        return self._snapshot_json

    @Slot(str, result=str)
    def dispatch(self, actionJson):
        try:
            action = json.loads(str(actionJson or "{}"))
            if not isinstance(action, dict):
                raise ValueError("Action must be a JSON object")
            if self._dispatch_callback is None:
                result = {"ok": False, "error": "No dispatch handler is registered"}
            else:
                result = self._dispatch_callback(action)
                if result is None:
                    result = {"ok": True}
                elif not isinstance(result, dict):
                    result = {"ok": True, "result": result}
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        self.refresh_snapshot()
        return json.dumps(result, ensure_ascii=True)

    @Slot()
    def requestRefresh(self):
        self._refresh_callback()

    @Slot(str)
    def openTracker(self, url):
        QDesktopServices.openUrl(QUrl(str(url or "")))

    @Slot(str)
    def openVtl(self, url):
        QDesktopServices.openUrl(QUrl(str(url or "")))

    @Slot(str)
    def copyText(self, text):
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(str(text or ""))

    @Slot(str)
    def openLoadout(self, player_key):
        self._loadout_callback(str(player_key or ""))

    @Slot(str)
    def togglePlayerFlag(self, puuid):
        self._flag_callback(str(puuid or ""))
        self.refresh_snapshot()

    def _window(self):
        parent = self.parent()
        return parent if parent is not None else None

    @Slot()
    def startWindowMove(self):
        window = self._window()
        if window is None:
            return
        start_move = getattr(window, "start_window_move", None)
        if callable(start_move):
            start_move()
            return
        window_handle = window.windowHandle() if hasattr(window, "windowHandle") else None
        if window_handle is not None and hasattr(window_handle, "startSystemMove"):
            window_handle.startSystemMove()

    @Slot()
    def maximizeWindow(self):
        window = self._window()
        if window is None:
            return
        if hasattr(window, "isMaximized") and window.isMaximized():
            return
        if hasattr(window, "showMaximized"):
            window.showMaximized()
        update = getattr(window, "update_window_control_states", None)
        if callable(update):
            update()

    @Slot()
    def toggleMaximizeRestore(self):
        window = self._window()
        if window is None:
            return
        toggle = getattr(window, "toggle_maximize_restore", None)
        if callable(toggle):
            toggle()
            return
        if hasattr(window, "isMaximized") and window.isMaximized():
            window.showNormal()
        elif hasattr(window, "showMaximized"):
            window.showMaximized()

    @Slot()
    def minimizeWindow(self):
        window = self._window()
        if window is not None and hasattr(window, "showMinimized"):
            window.showMinimized()

    @Slot()
    def closeWindow(self):
        window = self._window()
        if window is not None and hasattr(window, "close"):
            window.close()

    def refresh_snapshot(self, emit_signal=True):
        try:
            snapshot = self._snapshot_factory()
            self._snapshot_json = json.dumps(snapshot, ensure_ascii=True)
        except Exception as exc:
            print(f"[React Frontend] Failed to build snapshot: {exc}")
            self._snapshot_json = "{}"
        if emit_signal:
            self.snapshotChanged.emit(self._snapshot_json)
