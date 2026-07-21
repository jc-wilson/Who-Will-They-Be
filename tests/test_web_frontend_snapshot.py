import os
import tempfile
import unittest

from core.frontend_state import FrontendWindowState
from core.player_display import PlayerDisplayFormatter
from core.web_frontend_snapshot import build_web_frontend_snapshot


class DummyText:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class DummySwitch:
    def __init__(self, checked=False, enabled=True):
        self._checked = checked
        self._enabled = enabled

    def isChecked(self):
        return self._checked

    def isEnabled(self):
        return self._enabled


class DummyWindow:
    def __init__(self):
        self.current_theme_name = "midnight"
        self.current_theme_surface_mode = "opaque"
        self.THEME_DEFINITIONS = {
            "midnight": {"label": "WWTB", "swatch_a": "#111111", "swatch_b": "#222222"},
            "sage": {"label": "Sage", "swatch_a": "#333333", "swatch_b": "#444444"},
        }
        self.THEME_ORDER = ("midnight", "sage")
        self.MAP_DISPLAY_NAMES = {"map-a": "Ascent"}
        self.MAP_SPECIFIC_ROLE_TOKENS = {"Random", "Duelist"}
        self.window_state = FrontendWindowState()
        self.window_state.status_message = "Ready"
        self.window_state.loading_visible = True
        self.window_state.loading_progress = {"loaded": 1, "total": 3}
        self.window_state.set_web_modal("theme", {"source": "test"})
        self.window_state.queue_snipe_selected_friend = {
            "puuid": "friend-1",
            "display_name": "Friend#EUW",
        }
        self.window_state.queue_snipe_friends = [self.window_state.queue_snipe_selected_friend]
        self.window_state.loadout_editor = {
            "loading": False,
            "weapons": [{"weapon": "Vandal", "skinId": "skin-1"}],
            "presets": ["Current Loadout"],
            "selectedPreset": "Current Loadout",
        }
        self.window_state.player_loadout_modal = {
            "playerName": "Jett",
            "weapons": [{"weapon": "Vandal", "skinId": "skin-1"}],
        }
        self.window_state.restart_prompt = {"title": "Restart Riot Client"}
        self.window_state.left_players = [
            {
                "name": "Jett",
                "tag": "EUW",
                "agent": "Jett",
                "rank": "Gold 1",
                "kd": "1.2",
            }
        ]
        self.window_state.right_players = []
        self.window_state.map_agent_selection = {"Ascent": "Sova"}
        self.gamemode_value = DummyText("Competitive")
        self.server_value = DummyText("EU")
        self.starting_side_label = DummyText("STARTING SIDE: DEFENSE")
        self.agent_select_btn = DummyText("Jett")
        self.auto_lock_switch = DummySwitch(True)
        self.map_lock_switch = DummySwitch(False, False)
        self.queue_snipe_switch = DummySwitch(True)
        self.presence_mode_switch = DummySwitch(False, True)
        self.refresh_button = DummySwitch(True)
        self.dodge_button = DummySwitch(False)
        self.load_more_matches_button = DummySwitch(True)
        self.party_detection_enabled = True
        self.last_standard_agent_text = "Jett"
        self.owned_agent_handler = type("OwnedAgentHandler", (), {"combo": ["Random", "Jett"], "agents": ["Jett"]})()

    def agent_asset_url(self, agent_name):
        return f"file:///agents/{agent_name}.png"


class WebFrontendSnapshotTests(unittest.TestCase):
    def test_snapshot_contains_display_ready_state(self):
        window = DummyWindow()
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        for relative_path in (
            os.path.join("assets", "agents", "Jett.png"),
            os.path.join("assets", "ranks", "Gold 1.png"),
        ):
            full_path = os.path.join(temp_dir.name, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as handle:
                handle.write(b"png")

        snapshot = build_web_frontend_snapshot(
            window,
            theme_palette={"main": "#000000", "text": "#ffffff"},
            formatter=PlayerDisplayFormatter({}),
            resource_path_resolver=lambda relative_path: os.path.join(temp_dir.name, relative_path),
        )

        self.assertEqual(snapshot["themeName"], "midnight")
        self.assertEqual(snapshot["status"]["message"], "Ready")
        self.assertTrue(snapshot["status"]["loading"])
        self.assertEqual(snapshot["theme"]["options"][0]["name"], "midnight")
        self.assertEqual(snapshot["header"]["gamemode"], "Competitive")
        self.assertTrue(snapshot["header"]["canRefresh"])
        self.assertEqual(snapshot["agentLock"]["standardAgent"], "Jett")
        self.assertEqual(snapshot["agentLock"]["options"][1]["name"], "Jett")
        self.assertEqual(snapshot["mapAgents"]["maps"][0]["name"], "Ascent")
        self.assertEqual(snapshot["queueSnipe"]["selectedFriend"]["puuid"], "friend-1")
        self.assertEqual(snapshot["presence"]["mode"], "online")
        self.assertEqual(snapshot["tools"]["partyDetectionEnabled"], True)
        self.assertEqual(snapshot["ownedLoadoutEditor"]["weapons"][0]["weapon"], "Vandal")
        self.assertEqual(snapshot["playerLoadouts"]["playerName"], "Jett")
        self.assertEqual(snapshot["activeModal"], "theme")
        self.assertEqual(snapshot["prompts"]["restart"]["title"], "Restart Riot Client")
        self.assertEqual(snapshot["gamemode"], "Competitive")
        self.assertEqual(snapshot["server"], "EU")
        self.assertEqual(snapshot["selectedAgent"], "Jett")
        self.assertTrue(snapshot["autoLockEnabled"])
        self.assertFalse(snapshot["mapSpecificAvailable"])
        self.assertEqual(snapshot["mapAgentSelection"], {"Ascent": "Sova"})
        player = snapshot["leftPlayers"][0]
        self.assertEqual(player["displayName"], "Jett")
        self.assertEqual(player["name"], "Jett")
        self.assertEqual(player["tag"], "EUW")
        self.assertTrue(player["agentIcon"].startswith("file:///"))
        self.assertTrue(player["rankIcon"].startswith("file:///"))
        self.assertEqual(player["rrValue"], 0)
        self.assertEqual(player["rrMax"], 100)
        self.assertIn("recentRrChanges", player)
        self.assertIn("weapons", player)
        self.assertEqual(player["stats"]["kd"]["value"], "1.2")
        self.assertIn("trackerUrl", player)


if __name__ == "__main__":
    unittest.main()
