import os

from PySide6.QtCore import QUrl


try:
    from PySide6.QtWebChannel import QWebChannel
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception as exc:
    QWebChannel = None
    QWebEngineView = None
    WEBENGINE_IMPORT_ERROR = exc
else:
    WEBENGINE_IMPORT_ERROR = None


def web_frontend_available():
    return QWebChannel is not None and QWebEngineView is not None


def web_frontend_unavailable_reason():
    if web_frontend_available():
        return ""
    return f"Qt WebEngine/QWebChannel is unavailable: {WEBENGINE_IMPORT_ERROR}"


def create_web_frontend_view(dist_index_path, bridge, parent=None):
    if not web_frontend_available():
        raise RuntimeError(web_frontend_unavailable_reason())

    if not os.path.exists(dist_index_path):
        raise FileNotFoundError(
            f"React build not found at {dist_index_path}. Run npm install and npm run build in frontend_web."
        )

    view = QWebEngineView(parent)
    channel = QWebChannel(view.page())
    channel.registerObject("valScannerBridge", bridge)
    view.page().setWebChannel(channel)
    view.setUrl(QUrl.fromLocalFile(os.path.abspath(dist_index_path)))
    view._valscanner_web_channel = channel
    return view
