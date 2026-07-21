import os
import tempfile
import unittest

try:
    from PySide6.QtCore import QObject
except ImportError as exc:
    QObject = None
    PYSIDE_IMPORT_ERROR = exc
else:
    PYSIDE_IMPORT_ERROR = None

from core.frontend_state import FrontendWindowState


@unittest.skipIf(QObject is None, f"PySide6.QtCore unavailable: {PYSIDE_IMPORT_ERROR}")
class QmlProbeBridgeTests(unittest.TestCase):
    def test_properties_read_frontend_window_state(self):
        from frontend.qml_bridge import QmlProbeBridge

        state = FrontendWindowState({"selected_theme": "emberglass"})
        state.left_players = [{"name": "left-a"}, {"name": "left-b"}]
        state.right_players = [{"name": "right-a"}]
        bridge = QmlProbeBridge(state)

        self.assertEqual(bridge.appTitle, "ValScanner")
        self.assertEqual(bridge.currentThemeName, "emberglass")
        self.assertEqual(bridge.leftPlayerCount, 2)
        self.assertEqual(bridge.rightPlayerCount, 1)

    def test_request_refresh_emits_refresh_requested(self):
        from frontend.qml_bridge import QmlProbeBridge

        bridge = QmlProbeBridge(FrontendWindowState())
        emissions = []
        bridge.refreshRequested.connect(lambda: emissions.append(True))

        bridge.requestRefresh()

        self.assertEqual(emissions, [True])


@unittest.skipIf(QObject is None, f"PySide6.QtCore unavailable: {PYSIDE_IMPORT_ERROR}")
class PlayerCardBridgeTests(unittest.TestCase):
    def test_properties_build_player_cards_from_window_state(self):
        from frontend.qml_bridge import PlayerCardBridge

        state = FrontendWindowState({"flagged_players": {"p1": {"reason": "Avoid"}}})
        state.left_players = [{"puuid": "p1", "name": "Left#EUW", "rank": "[]"}]
        state.right_players = [{"name": "Right#EUW", "kd": 1.2}]

        bridge = PlayerCardBridge(
            state,
            resource_path_resolver=lambda relative_path: f"C:\\missing\\{relative_path}",
        )

        self.assertEqual(len(bridge.leftPlayerCards), 1)
        self.assertEqual(len(bridge.rightPlayerCards), 1)
        self.assertEqual(bridge.leftPlayerCards[0]["displayName"], "Left#EUW")
        self.assertTrue(bridge.leftPlayerCards[0]["isFlagged"])
        self.assertEqual(bridge.leftPlayerCards[0]["flagTooltip"], "Avoid")
        self.assertEqual(bridge.rightPlayerCards[0]["kdText"], "1.2")

    def test_player_icon_resolver_is_included_in_card_model(self):
        from frontend.qml_bridge import PlayerCardBridge

        state = FrontendWindowState()
        state.left_players = [{"puuid": "p1", "name": "Left#EUW"}]

        bridge = PlayerCardBridge(
            state,
            player_icon_resolver=lambda player: {
                "iconPath": "C:\\icons\\p1.png",
                "tooltip": f"Icon for {player['puuid']}",
            },
        )

        self.assertEqual(bridge.leftPlayerCards[0]["playerIconPath"], "C:\\icons\\p1.png")
        self.assertEqual(bridge.leftPlayerCards[0]["playerIconTooltip"], "Icon for p1")

    def test_copy_and_open_slots_use_injected_callbacks(self):
        from frontend.qml_bridge import PlayerCardBridge

        opened = []
        copied = []
        loadouts = []
        flags = []
        bridge = PlayerCardBridge(
            FrontendWindowState(),
            open_callback=opened.append,
            copy_callback=copied.append,
            loadout_callback=loadouts.append,
            flag_callback=flags.append,
        )

        bridge.openTracker("https://tracker.example/player")
        bridge.openVtl("https://vtl.lol/id/player")
        bridge.copyName("Name#Tag")
        bridge.openLoadout("player-key")
        bridge.toggleFlag("player-puuid")

        self.assertEqual(opened, ["https://tracker.example/player", "https://vtl.lol/id/player"])
        self.assertEqual(copied, ["Name#Tag"])
        self.assertEqual(loadouts, ["player-key"])
        self.assertEqual(flags, ["player-puuid"])

    def test_style_colors_are_exposed_and_update_with_signal(self):
        from frontend.qml_bridge import PlayerCardBridge

        bridge = PlayerCardBridge(FrontendWindowState(), style_colors={"card": "#111111"})
        emissions = []
        bridge.dataChanged.connect(lambda: emissions.append(True))

        self.assertEqual(bridge.styleColors["card"], "#111111")

        bridge.set_style_colors({"card": "#222222", "text": "#ffffff"})

        self.assertEqual(bridge.styleColors["card"], "#222222")
        self.assertEqual(bridge.styleColors["text"], "#ffffff")
        self.assertEqual(emissions, [True])

    def test_refresh_emits_data_changed_and_updates_properties(self):
        from frontend.qml_bridge import PlayerCardBridge

        state = FrontendWindowState()
        bridge = PlayerCardBridge(state)
        emissions = []
        bridge.dataChanged.connect(lambda: emissions.append(True))

        state.left_players = [{"name": "Updated"}]
        bridge.refresh()

        self.assertEqual(len(bridge.leftPlayerCards), 1)
        self.assertEqual(bridge.leftPlayerCards[0]["displayName"], "Updated")
        self.assertEqual(emissions, [True])

    def test_qml_player_icon_cache_path_is_stable_and_local(self):
        from frontend.QApplication import qml_player_icon_cache_path

        with tempfile.TemporaryDirectory() as temp_dir:
            first_path = qml_player_icon_cache_path("  P1  ", cache_dir=temp_dir)
            second_path = qml_player_icon_cache_path("p1", cache_dir=temp_dir)

        self.assertEqual(first_path, second_path)
        self.assertTrue(first_path.endswith(".png"))

    def test_qml_player_icon_resolver_writes_pixmap_to_local_path(self):
        from frontend.QApplication import ValorantStatsWindow, qml_player_icon_cache_path

        class FakePixmap:
            def __init__(self):
                self.saved = None

            def isNull(self):
                return False

            def save(self, path, image_format):
                self.saved = (path, image_format)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as handle:
                    handle.write(b"png")
                return True

        class FakeWindow:
            def __init__(self, pixmap):
                self.pixmap = pixmap

            def player_icon_for_player(self, player):
                if player.get("puuid") == "p1":
                    return self.pixmap, "Known player"
                return None

        pixmap = FakePixmap()
        window = FakeWindow(pixmap)

        result = ValorantStatsWindow.qml_player_icon_for_player(window, {"puuid": "p1"})

        self.assertEqual(result["tooltip"], "Known player")
        self.assertEqual(result["iconPath"], qml_player_icon_cache_path("p1"))
        self.assertEqual(pixmap.saved, (result["iconPath"], "PNG"))
        self.assertTrue(os.path.exists(result["iconPath"]))
        self.assertEqual(ValorantStatsWindow.qml_player_icon_for_player(window, {"puuid": "missing"}), {})


@unittest.skipIf(QObject is None, f"PySide6.QtCore unavailable: {PYSIDE_IMPORT_ERROR}")
class TopBarBridgeTests(unittest.TestCase):
    class FakeWidget:
        def __init__(self, text="", checked=False, enabled=True, visible=False):
            self._text = text
            self._checked = checked
            self._enabled = enabled
            self._visible = visible

        def text(self):
            return self._text

        def setText(self, text):
            self._text = text

        def isChecked(self):
            return self._checked

        def setChecked(self, checked):
            self._checked = bool(checked)

        def isEnabled(self):
            return self._enabled

        def setEnabled(self, enabled):
            self._enabled = bool(enabled)

        def isVisible(self):
            return self._visible

        def setVisible(self, visible):
            self._visible = bool(visible)

    class FakeWindow:
        def __init__(self):
            self.calls = []
            self.gamemode_value = TopBarBridgeTests.FakeWidget("Competitive")
            self.server_value = TopBarBridgeTests.FakeWidget("EU")
            self.starting_side_label = TopBarBridgeTests.FakeWidget("Starting Side: Attack")
            self.agent_select_btn = TopBarBridgeTests.FakeWidget("Jett")
            self.auto_lock_switch = TopBarBridgeTests.FakeWidget(checked=True)
            self.map_lock_switch = TopBarBridgeTests.FakeWidget(checked=False, enabled=True)
            self.refresh_button = TopBarBridgeTests.FakeWidget(enabled=True)
            self.load_more_matches_button = TopBarBridgeTests.FakeWidget(enabled=False)
            self.dodge_button = TopBarBridgeTests.FakeWidget(enabled=True)
            self.lock_agent_button = TopBarBridgeTests.FakeWidget(enabled=True)
            self.presence_mode_indicator = TopBarBridgeTests.FakeWidget(visible=True)
            self.get_agent_asset_path = lambda agent_name: f"C:\\agents\\{agent_name}.png"
            self.get_asset_icon_path = lambda filename: f"C:\\icons\\{filename}"

        def on_auto_lock_toggled(self, checked):
            self.calls.append(("auto", checked))

        def on_map_lock_toggled(self, checked):
            self.calls.append(("map", checked))

        def run_valo_stats(self):
            self.calls.append("refresh")

        def open_agent_popup(self):
            self.calls.append("agent")

        def instalock_agent(self):
            self.calls.append("lock")

        def run_dodge_button(self):
            self.calls.append("dodge")

        def run_load_more_matches_button(self):
            self.calls.append("load_more")

        def open_user_loadouts(self):
            self.calls.append("loadouts")

        def open_tools_popup(self):
            self.calls.append("tools")

        def open_tools_popup_with_rect(self, rect):
            self.calls.append(("tools_rect", rect))

    def test_properties_read_widget_backing_state(self):
        from frontend.qml_bridge import TopBarBridge

        window = self.FakeWindow()
        bridge = TopBarBridge(window, style_colors={"card": "#111111"}, logo_path="C:\\logo.png")

        self.assertEqual(bridge.theme["card"], "#111111")
        self.assertEqual(bridge.logoPath, "file:///C:/logo.png")
        self.assertEqual(bridge.lockIconPath, "file:///C:/icons/lock-solid.png")
        self.assertEqual(bridge.dodgeIconPath, "file:///C:/icons/arrow-right-from-bracket-solid.png")
        self.assertEqual(bridge.loadMoreIconPath, "file:///C:/icons/plus-solid.png")
        self.assertEqual(bridge.loadoutsIconPath, "file:///C:/icons/briefcase-solid.png")
        self.assertEqual(bridge.toolsIconPath, "file:///C:/icons/wrench-solid.png")
        self.assertEqual(bridge.refreshIconPath, "file:///C:/icons/refresh.png")
        self.assertEqual(bridge.chevronDownIconPath, "file:///C:/icons/chevron-down-solid.png")
        self.assertEqual(bridge.gamemode, "Competitive")
        self.assertEqual(bridge.server, "EU")
        self.assertEqual(bridge.startingSideText, "Starting Side: Attack")
        self.assertEqual(bridge.selectedAgent, "Jett")
        self.assertEqual(bridge.selectedAgentIconPath, "file:///C:/agents/Jett.png")
        self.assertTrue(bridge.autoLockEnabled)
        self.assertFalse(bridge.mapSpecificEnabled)
        self.assertTrue(bridge.mapSpecificAvailable)
        self.assertTrue(bridge.refreshEnabled)
        self.assertFalse(bridge.loadMoreEnabled)
        self.assertTrue(bridge.dodgeEnabled)
        self.assertTrue(bridge.lockEnabled)
        self.assertTrue(bridge.appearOfflineVisible)

    def test_app_action_slots_call_window_methods(self):
        from frontend.qml_bridge import TopBarBridge

        window = self.FakeWindow()
        bridge = TopBarBridge(window)

        bridge.openAgentSelector()
        bridge.lockAgent()
        bridge.dodgeGame()
        bridge.loadMoreGames()
        bridge.openLoadouts()
        bridge.openTools()
        bridge.refresh()

        self.assertEqual(window.calls, ["agent", "lock", "dodge", "load_more", "loadouts", "tools", "refresh"])

    def test_open_tools_at_passes_anchor_rect(self):
        from frontend.qml_bridge import TopBarBridge

        window = self.FakeWindow()
        window.open_tools_popup = lambda rect=None: window.calls.append(("tools", rect))
        bridge = TopBarBridge(window)

        bridge.openToolsAt({"x": 10, "y": 20, "width": 72, "height": 38})

        self.assertEqual(window.calls, [("tools", {"x": 10, "y": 20, "width": 72, "height": 38})])

    def test_toggle_slots_update_backing_switches_and_emit(self):
        from frontend.qml_bridge import TopBarBridge

        window = self.FakeWindow()
        bridge = TopBarBridge(window)
        emissions = []
        bridge.dataChanged.connect(lambda: emissions.append(True))

        bridge.setAutoLockEnabled(False)
        bridge.setMapSpecificEnabled(True)

        self.assertFalse(window.auto_lock_switch.isChecked())
        self.assertTrue(window.map_lock_switch.isChecked())
        self.assertEqual(emissions, [True, True])

    def test_notify_and_style_updates_emit_data_changed(self):
        from frontend.qml_bridge import TopBarBridge

        bridge = TopBarBridge(self.FakeWindow(), style_colors={"card": "#111111"})
        emissions = []
        bridge.dataChanged.connect(lambda: emissions.append(True))

        bridge.notify_bindings()
        bridge.set_style_colors({"card": "#222222"})

        self.assertEqual(bridge.theme["card"], "#222222")
        self.assertEqual(emissions, [True, True])


@unittest.skipIf(QObject is None, f"PySide6.QtCore unavailable: {PYSIDE_IMPORT_ERROR}")
class ThemePopupBridgeTests(unittest.TestCase):
    def make_bridge(self, selected_theme="emberglass", surface_mode="transparent"):
        from frontend.QApplication import (
            THEME_DEFINITIONS,
            THEME_ORDER,
            normalize_theme_name,
            normalize_theme_surface_mode,
        )
        from frontend.qml_bridge import ThemePopupBridge

        self.selected_themes = []
        self.selected_surface_modes = []
        self.close_calls = []
        return ThemePopupBridge(
            THEME_DEFINITIONS,
            THEME_ORDER,
            selected_theme,
            surface_mode,
            self.selected_themes.append,
            self.selected_surface_modes.append,
            lambda: self.close_calls.append(True),
            {"text": "#ffffff", "accent": "#abcdef"},
            normalize_theme_name=normalize_theme_name,
            normalize_surface_mode=normalize_theme_surface_mode,
        )

    def test_theme_options_match_theme_order(self):
        from frontend.QApplication import THEME_ORDER

        bridge = self.make_bridge()

        self.assertEqual([option["name"] for option in bridge.themeOptions], list(THEME_ORDER))

    def test_theme_options_use_theme_definitions(self):
        from frontend.QApplication import THEME_DEFINITIONS

        bridge = self.make_bridge(selected_theme="sage")
        options_by_name = {option["name"]: option for option in bridge.themeOptions}

        for theme_name, theme_definition in THEME_DEFINITIONS.items():
            option = options_by_name[theme_name]
            self.assertEqual(option["label"], theme_definition["label"])
            self.assertEqual(option["swatchA"], theme_definition["swatch_a"])
            self.assertEqual(option["swatchB"], theme_definition["swatch_b"])
            self.assertEqual(option["main"], theme_definition["main"])
            self.assertEqual(option["panel"], theme_definition["panel"])
            self.assertEqual(option["card"], theme_definition["card"])
            self.assertEqual(option["cardAlt"], theme_definition["card_alt"])
            self.assertEqual(option["border"], theme_definition["border"])
            self.assertEqual(option["borderSoft"], theme_definition["border_soft"])
            self.assertEqual(option["text"], theme_definition["text"])
            self.assertEqual(option["muted"], theme_definition["muted"])
            self.assertEqual(option["accent"], theme_definition["accent"])
            self.assertEqual(option["accentHover"], theme_definition["accent_hover"])
            self.assertEqual(option["selected"], theme_name == "sage")

    def test_select_theme_calls_callback_with_normalized_theme(self):
        bridge = self.make_bridge()

        bridge.selectTheme("SAGE")

        self.assertEqual(self.selected_themes, ["sage"])
        self.assertTrue(
            next(option for option in bridge.themeOptions if option["name"] == "sage")["selected"]
        )

    def test_surface_mode_changes_call_callback_with_normalized_mode(self):
        bridge = self.make_bridge(surface_mode="transparent")

        bridge.setSurfaceMode("opaque")
        bridge.setSurfaceMode("transparent")

        self.assertEqual(self.selected_surface_modes, ["opaque", "transparent"])
        self.assertEqual(bridge.surfaceMode, "transparent")
        self.assertFalse(bridge.opaqueSurface)


if __name__ == "__main__":
    unittest.main()
