import unittest

from core.frontend_state import FrontendWindowState


class FrontendWindowStateTests(unittest.TestCase):
    def test_dict_and_list_player_inputs_preserve_order(self):
        state = FrontendWindowState()
        dict_players = {
            "first": {"name": "A", "team": "Red"},
            "second": {"name": "B", "team": "Blue"},
        }
        list_players = [{"name": "C"}, {"name": "D"}]

        self.assertEqual(
            [player["name"] for player in state.normalize_players(dict_players)],
            ["A", "B"],
        )
        self.assertEqual(
            [player["name"] for player in state.normalize_players(list_players)],
            ["C", "D"],
        )

    def test_deathmatch_splitting_matches_odd_even_behavior(self):
        state = FrontendWindowState()
        players = [{"name": str(index)} for index in range(5)]

        _, left, right = state.split_players(players, gamemode="Deathmatch")

        self.assertEqual([player["name"] for player in left], ["0", "2", "4"])
        self.assertEqual([player["name"] for player in right], ["1", "3"])

    def test_red_blue_splitting_ignores_other_teams(self):
        state = FrontendWindowState()
        players = [
            {"name": "red", "team": "Red"},
            {"name": "other", "team": "Green"},
            {"name": "blue", "team": "Blue"},
        ]

        _, left, right = state.split_players(players, gamemode="Competitive")

        self.assertEqual([player["name"] for player in left], ["red"])
        self.assertEqual([player["name"] for player in right], ["blue"])

    def test_starting_side_label_text(self):
        players = [
            {"puuid": "self-red", "team": "Red"},
            {"puuid": "self-blue", "team": "Blue"},
        ]

        self.assertEqual(
            FrontendWindowState.starting_side_label_text(players, "self-red"),
            "STARTING SIDE: ATTACK",
        )
        self.assertEqual(
            FrontendWindowState.starting_side_label_text(players, "self-blue"),
            "STARTING SIDE: DEFENSE",
        )
        self.assertEqual(
            FrontendWindowState.starting_side_label_text(players, "missing"),
            "",
        )

    def test_saved_payload_preserves_plain_state_values(self):
        friend = {
            "puuid": "friend-puuid",
            "game_name": "Jett",
            "game_tag": "NA1",
            "display_name": "Jett#NA1",
        }
        state = FrontendWindowState(
            {
                "flagged_players": {"flagged": {"reason": "reason"}},
                "co_play_history": {"by_user": {"self": {"matches": {}, "counts": {}}}},
                "map_agent_selection": {"map-a": "Sova"},
                "theme_surface_mode": "opaque",
                "presence_mode": "offline",
                "queue_snipe_selected_friend": friend,
            }
        )

        payload = state.build_saved_payload(
            selected_theme="midnight",
            theme_surface_mode=state.current_theme_surface_mode,
            presence_mode=state.presence_mode,
            selected_standard_agent="Random",
            auto_lock_enabled=True,
            map_lock_enabled=True,
            queue_snipe_enabled=True,
            queue_snipe_selected_friend=state.queue_snipe_selected_friend,
        )

        self.assertEqual(payload["flagged_players"], {"flagged": {"reason": "reason"}})
        self.assertEqual(payload["co_play_history"], {"by_user": {"self": {"matches": {}, "counts": {}}}})
        self.assertEqual(payload["map_agent_selection"], {"map-a": "Sova"})
        self.assertEqual(payload["theme_surface_mode"], "opaque")
        self.assertEqual(payload["presence_mode"], "offline")
        self.assertEqual(payload["queue_snipe_selected_friend"]["display_name"], "Jett#NA1")
        self.assertTrue(payload["queue_snipe_enabled"])


if __name__ == "__main__":
    unittest.main()
