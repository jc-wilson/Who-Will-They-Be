import unittest

from core.player_display import PlayerDisplayFormatter


class PlayerDisplayFormatterTests(unittest.TestCase):
    def test_tracker_url_percent_encodes_riot_id(self):
        formatter = PlayerDisplayFormatter()

        self.assertEqual(
            formatter.build_tracker_url("Name With Space#EU/W"),
            "https://tracker.gg/valorant/profile/riot/Name%20With%20Space%23EU%2FW",
        )

    def test_clipboard_name_prefers_game_name_and_tag_then_display_then_unknown(self):
        formatter = PlayerDisplayFormatter()

        self.assertEqual(
            formatter.build_player_clipboard_name({"game_name": "Neon", "tag": "EUW"}),
            "Neon#EUW",
        )
        self.assertEqual(
            formatter.build_player_clipboard_name({"display_name": "Fallback"}),
            "Fallback",
        )
        self.assertEqual(formatter.build_player_clipboard_name({}), "Unknown")

    def test_flag_tooltip_for_missing_empty_and_populated_reason(self):
        formatter = PlayerDisplayFormatter(
            {
                "empty": {"reason": ""},
                "filled": {"reason": "Dodged twice"},
            }
        )

        self.assertEqual(
            formatter.get_flag_tooltip_for_player({"puuid": "missing"}),
            "Toggle flagged player",
        )
        self.assertEqual(
            formatter.get_flag_tooltip_for_player({"puuid": "empty"}),
            "Flagged player",
        )
        self.assertEqual(
            formatter.get_flag_tooltip_for_player({"puuid": "filled"}),
            "Dodged twice",
        )

    def test_stat_colour_thresholds(self):
        formatter = PlayerDisplayFormatter()

        self.assertEqual(formatter.stat_colour_category("46%", "wl"), "red")
        self.assertEqual(formatter.stat_colour_category("47%", "wl"), "gold")
        self.assertEqual(formatter.stat_colour_category("53%", "wl"), "limegreen")
        self.assertEqual(formatter.stat_colour_category("60%", "wl"), "cyan")

        self.assertEqual(formatter.stat_colour_category(199, "acs"), "red")
        self.assertEqual(formatter.stat_colour_category(200, "acs"), "gold")
        self.assertEqual(formatter.stat_colour_category(225, "acs"), "limegreen")
        self.assertEqual(formatter.stat_colour_category(250, "acs"), "cyan")

        self.assertEqual(formatter.stat_colour_category(0.89, "kd"), "red")
        self.assertEqual(formatter.stat_colour_category(0.9, "kd"), "gold")
        self.assertEqual(formatter.stat_colour_category(1.1, "kd"), "limegreen")
        self.assertEqual(formatter.stat_colour_category(1.25, "kd"), "cyan")

        self.assertEqual(formatter.stat_colour_category(19, "hs"), "red")
        self.assertEqual(formatter.stat_colour_category(20, "hs"), "gold")
        self.assertEqual(formatter.stat_colour_category(30, "hs"), "limegreen")
        self.assertEqual(formatter.stat_colour_category(40, "hs"), "cyan")

    def test_buddy_id_extraction_from_scalar_list_and_dict_payloads(self):
        formatter = PlayerDisplayFormatter()

        self.assertEqual(formatter.extract_buddy_id_from_skin_data("buddy-a"), "buddy-a")
        self.assertEqual(formatter.extract_buddy_id_from_skin_data(["skin", "buddy-b"]), "buddy-b")
        self.assertEqual(
            formatter.extract_buddy_id_from_skin_data(["skin", {"CharmID": "buddy-c"}]),
            "buddy-c",
        )
        self.assertEqual(
            formatter.extract_buddy_id_from_skin_data({"CharmLevelID": "buddy-d"}),
            "buddy-d",
        )

        self.assertTrue(
            formatter.player_has_buddy_equipped(
                {"skins": {"Vandal": ["skin", {"CharmID": "Buddy-X"}]}},
                "buddy-x",
            )
        )


if __name__ == "__main__":
    unittest.main()
