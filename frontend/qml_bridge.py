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
            )
            self._right_player_cards = build_player_card_displays(
                getattr(self._window_state, "right_players", []) or [],
                formatter=self._formatter,
                flagged_players=flagged_players,
                resource_path_resolver=self._resource_path_resolver,
            )
        except Exception as exc:
            print(f"[QML PlayerCard Prototype] model generation failed: {exc}")
            self._left_player_cards = []
            self._right_player_cards = []
        self.dataChanged.emit()

    def set_style_colors(self, style_colors):
        self._style_colors = dict(style_colors or {})
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
