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
