import os

from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication

from core.player_card_display import build_player_card_displays


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


class PlayerCardBridge(QObject):
    dataChanged = Signal()

    def __init__(
        self,
        window_state,
        *,
        formatter=None,
        resource_path_resolver=None,
        player_icon_resolver=None,
        style_colors=None,
        open_callback=None,
        copy_callback=None,
        loadout_callback=None,
        flag_callback=None,
        parent=None,
    ):
        super().__init__(parent)
        self._window_state = window_state
        self._formatter = formatter
        self._resource_path_resolver = resource_path_resolver
        self._player_icon_resolver = player_icon_resolver
        self._style_colors = dict(style_colors or {})
        self._open_callback = open_callback or self._open_url
        self._copy_callback = copy_callback or self._copy_to_clipboard
        self._loadout_callback = loadout_callback or (lambda player_key: None)
        self._flag_callback = flag_callback or (lambda puuid: None)
        self._left_player_cards = []
        self._right_player_cards = []
        self.refresh()

    @staticmethod
    def _open_url(url):
        QDesktopServices.openUrl(QUrl(str(url or "")))

    @staticmethod
    def _copy_to_clipboard(text):
        clipboard = QGuiApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(str(text or ""))

    @Property("QVariantList", notify=dataChanged)
    def leftPlayerCards(self):
        return list(self._left_player_cards)

    @Property("QVariantList", notify=dataChanged)
    def rightPlayerCards(self):
        return list(self._right_player_cards)

    @Property("QVariantMap", notify=dataChanged)
    def styleColors(self):
        return dict(self._style_colors)

    @Slot(str)
    def openTracker(self, trackerUrl):
        self._open_callback(str(trackerUrl or ""))

    @Slot(str)
    def openVtl(self, vtlUrl):
        self._open_callback(str(vtlUrl or ""))

    @Slot(str)
    def copyName(self, clipboardName):
        self._copy_callback(str(clipboardName or ""))

    @Slot(str)
    def openLoadout(self, playerKey):
        self._loadout_callback(str(playerKey or ""))

    @Slot(str)
    def toggleFlag(self, puuid):
        self._flag_callback(str(puuid or ""))

    def refresh(self):
        flagged_players = getattr(self._window_state, "flagged_players", {})
        try:
            if self._formatter is not None:
                self._formatter.set_flagged_players(flagged_players)
            self._left_player_cards = build_player_card_displays(
                getattr(self._window_state, "left_players", []) or [],
                formatter=self._formatter,
                flagged_players=flagged_players,
                resource_path_resolver=self._resource_path_resolver,
                player_icon_resolver=self._player_icon_resolver,
            )
            self._right_player_cards = build_player_card_displays(
                getattr(self._window_state, "right_players", []) or [],
                formatter=self._formatter,
                flagged_players=flagged_players,
                resource_path_resolver=self._resource_path_resolver,
                player_icon_resolver=self._player_icon_resolver,
            )
        except Exception as exc:
            print(f"[QML PlayerCard Prototype] model generation failed: {exc}")
            self._left_player_cards = []
            self._right_player_cards = []
        self.dataChanged.emit()

    def set_style_colors(self, style_colors):
        self._style_colors = dict(style_colors or {})
        self.dataChanged.emit()


class TopBarBridge(QObject):
    dataChanged = Signal()

    def __init__(self, window, style_colors=None, logo_path="", parent=None):
        super().__init__(parent)
        self._window = window
        self._style_colors = dict(style_colors or {})
        self._logo_path = str(logo_path or "")
        self._background_path = ""

    @staticmethod
    def _widget_text(widget, fallback=""):
        if widget is None or not hasattr(widget, "text"):
            return fallback
        return str(widget.text() or fallback)

    @staticmethod
    def _widget_checked(widget):
        if widget is None or not hasattr(widget, "isChecked"):
            return False
        return bool(widget.isChecked())

    @staticmethod
    def _widget_enabled(widget, default=True):
        if widget is None or not hasattr(widget, "isEnabled"):
            return default
        return bool(widget.isEnabled())

    def _asset_url(self, filename):
        resolver = getattr(self._window, "get_asset_icon_path", None)
        icon_path = resolver(filename) if callable(resolver) else os.path.join("assets", filename)
        return QUrl.fromLocalFile(str(icon_path or "")).toString() if icon_path else ""

    @Property("QVariantMap", notify=dataChanged)
    def theme(self):
        return dict(self._style_colors)

    @Property(str, notify=dataChanged)
    def logoPath(self):
        return QUrl.fromLocalFile(self._logo_path).toString() if self._logo_path else ""

    @Property(str, notify=dataChanged)
    def backgroundPath(self):
        return str(self._background_path or "")

    @Property(str, notify=dataChanged)
    def lockIconPath(self):
        return self._asset_url("lock-solid.png")

    @Property(str, notify=dataChanged)
    def dodgeIconPath(self):
        return self._asset_url("arrow-right-from-bracket-solid.png")

    @Property(str, notify=dataChanged)
    def loadMoreIconPath(self):
        return self._asset_url("plus-solid.png")

    @Property(str, notify=dataChanged)
    def loadoutsIconPath(self):
        return self._asset_url("briefcase-solid.png")

    @Property(str, notify=dataChanged)
    def toolsIconPath(self):
        return self._asset_url("wrench-solid.png")

    @Property(str, notify=dataChanged)
    def refreshIconPath(self):
        return self._asset_url("refresh.png")

    @Property(str, notify=dataChanged)
    def chevronDownIconPath(self):
        return self._asset_url("chevron-down-solid.png")

    @Property(str, notify=dataChanged)
    def gamemode(self):
        return self._widget_text(getattr(self._window, "gamemode_value", None), "Unknown")

    @Property(str, notify=dataChanged)
    def server(self):
        return self._widget_text(getattr(self._window, "server_value", None), "Unknown")

    @Property(str, notify=dataChanged)
    def startingSideText(self):
        return self._widget_text(getattr(self._window, "starting_side_label", None), "")

    @Property(str, notify=dataChanged)
    def selectedAgent(self):
        return self._widget_text(getattr(self._window, "agent_select_btn", None), "Random")

    @Property(str, notify=dataChanged)
    def selectedAgentIconPath(self):
        agent_name = self.selectedAgent
        resolver = getattr(self._window, "get_agent_asset_path", None)
        if callable(resolver):
            icon_path = resolver(agent_name)
        else:
            icon_path = os.path.join("assets", "agents", f"{str(agent_name).replace('/', '_')}.png")
        return QUrl.fromLocalFile(str(icon_path or "")).toString() if icon_path else ""

    @Property(bool, notify=dataChanged)
    def autoLockEnabled(self):
        return self._widget_checked(getattr(self._window, "auto_lock_switch", None))

    @Property(bool, notify=dataChanged)
    def mapSpecificEnabled(self):
        return self._widget_checked(getattr(self._window, "map_lock_switch", None))

    @Property(bool, notify=dataChanged)
    def mapSpecificAvailable(self):
        return self._widget_enabled(getattr(self._window, "map_lock_switch", None), False)

    @Property(bool, notify=dataChanged)
    def refreshEnabled(self):
        return self._widget_enabled(getattr(self._window, "refresh_button", None), True)

    @Property(bool, notify=dataChanged)
    def loadMoreEnabled(self):
        return self._widget_enabled(getattr(self._window, "load_more_matches_button", None), False)

    @Property(bool, notify=dataChanged)
    def dodgeEnabled(self):
        return self._widget_enabled(getattr(self._window, "dodge_button", None), True)

    @Property(bool, notify=dataChanged)
    def lockEnabled(self):
        return self._widget_enabled(getattr(self._window, "lock_agent_button", None), True)

    @Property(bool, notify=dataChanged)
    def appearOfflineVisible(self):
        indicator = getattr(self._window, "presence_mode_indicator", None)
        if indicator is not None and hasattr(indicator, "isVisible"):
            return bool(indicator.isVisible())
        presence_mode = str(getattr(self._window, "presence_mode", "") or "").strip().lower()
        return presence_mode == "offline"

    @Slot()
    def openAgentSelector(self):
        self._window.open_agent_popup()

    @Slot()
    def lockAgent(self):
        self._window.instalock_agent()

    @Slot(bool)
    def setAutoLockEnabled(self, checked):
        switch = getattr(self._window, "auto_lock_switch", None)
        if switch is not None:
            switch.setChecked(bool(checked))
        else:
            self._window.on_auto_lock_toggled(bool(checked))
        self.dataChanged.emit()

    @Slot(bool)
    def setMapSpecificEnabled(self, checked):
        switch = getattr(self._window, "map_lock_switch", None)
        if switch is not None and self._widget_enabled(switch, False):
            switch.setChecked(bool(checked))
        elif switch is None:
            self._window.on_map_lock_toggled(bool(checked))
        self.dataChanged.emit()

    @Slot()
    def dodgeGame(self):
        self._window.run_dodge_button()

    @Slot()
    def loadMoreGames(self):
        self._window.run_load_more_matches_button()

    @Slot()
    def openLoadouts(self):
        self._window.open_user_loadouts()

    @Slot()
    def openTools(self):
        self._window.open_tools_popup()

    @Slot("QVariantMap")
    def openToolsAt(self, anchorRect):
        rect = dict(anchorRect or {})
        self._window.open_tools_popup(rect)

    @Slot()
    def refresh(self):
        self._window.run_valo_stats()

    def set_style_colors(self, style_colors):
        self._style_colors = dict(style_colors or {})
        self.dataChanged.emit()

    def set_logo_path(self, logo_path):
        self._logo_path = str(logo_path or "")
        self.dataChanged.emit()

    def set_background_path(self, background_path):
        self._background_path = str(background_path or "")
        self.dataChanged.emit()

    def notify_bindings(self):
        self.dataChanged.emit()


class ThemePopupBridge(QObject):
    dataChanged = Signal()

    def __init__(
        self,
        theme_definitions,
        theme_order,
        current_theme_name,
        current_surface_mode,
        on_theme_selected,
        on_surface_mode_selected,
        on_close_popup,
        style_colors=None,
        close_icon_path="",
        normalize_theme_name=None,
        normalize_surface_mode=None,
        parent=None,
    ):
        super().__init__(parent)
        self._theme_definitions = theme_definitions
        self._theme_order = tuple(theme_order)
        self._normalize_theme_name = normalize_theme_name or (lambda name: str(name or "").strip().lower())
        self._normalize_surface_mode = normalize_surface_mode or (
            lambda mode: "opaque" if str(mode or "").strip().lower() == "opaque" else "transparent"
        )
        self._current_theme_name = self._normalize_theme_name(current_theme_name)
        self._surface_mode = self._normalize_surface_mode(current_surface_mode)
        self._on_theme_selected = on_theme_selected
        self._on_surface_mode_selected = on_surface_mode_selected
        self._on_close_popup = on_close_popup
        self._style_colors = dict(style_colors or {})
        self._close_icon_path = str(close_icon_path or "")

    @Property("QVariantList", notify=dataChanged)
    def themeOptions(self):
        return [
            {
                "name": theme_name,
                "label": self._theme_definitions[theme_name]["label"],
                "swatchA": self._theme_definitions[theme_name]["swatch_a"],
                "swatchB": self._theme_definitions[theme_name]["swatch_b"],
                "main": self._theme_definitions[theme_name]["main"],
                "panel": self._theme_definitions[theme_name]["panel"],
                "card": self._theme_definitions[theme_name]["card"],
                "cardAlt": self._theme_definitions[theme_name]["card_alt"],
                "border": self._theme_definitions[theme_name]["border"],
                "borderSoft": self._theme_definitions[theme_name]["border_soft"],
                "text": self._theme_definitions[theme_name]["text"],
                "muted": self._theme_definitions[theme_name]["muted"],
                "accent": self._theme_definitions[theme_name]["accent"],
                "accentHover": self._theme_definitions[theme_name]["accent_hover"],
                "selected": theme_name == self._current_theme_name,
            }
            for theme_name in self._theme_order
        ]

    @Property(str, notify=dataChanged)
    def surfaceMode(self):
        return self._surface_mode

    @Property(bool, notify=dataChanged)
    def opaqueSurface(self):
        return self._surface_mode == "opaque"

    @Property("QVariantMap", notify=dataChanged)
    def styleColors(self):
        return dict(self._style_colors)

    @Property(str, notify=dataChanged)
    def closeIconPath(self):
        return QUrl.fromLocalFile(self._close_icon_path).toString() if self._close_icon_path else ""

    @Slot(str)
    def selectTheme(self, name):
        normalized_theme_name = self._normalize_theme_name(name)
        self._current_theme_name = normalized_theme_name
        self._on_theme_selected(normalized_theme_name)
        self.dataChanged.emit()

    @Slot(str)
    def setSurfaceMode(self, surfaceMode):
        normalized_surface_mode = self._normalize_surface_mode(surfaceMode)
        self._surface_mode = normalized_surface_mode
        self._on_surface_mode_selected(normalized_surface_mode)
        self.dataChanged.emit()

    @Slot()
    def closePopup(self):
        self._on_close_popup()

    def refresh_theme_state(self, theme_name, surface_mode, style_colors=None):
        self._current_theme_name = self._normalize_theme_name(theme_name)
        self._surface_mode = self._normalize_surface_mode(surface_mode)
        if style_colors is not None:
            self._style_colors = dict(style_colors)
        self.dataChanged.emit()
