import os
import tempfile
import unittest

from core.player_card_display import SPECIAL_BUDDY_UUID, build_player_card_display
from core.player_display import PlayerDisplayFormatter


class PlayerCardDisplayTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        for relative_path in (
            os.path.join("assets", "agents", "Jett.png"),
            os.path.join("assets", "ranks", "Gold 2.png"),
            os.path.join("assets", "ranks", "Unranked.png"),
            os.path.join("assets", "skins", "vandal-skin.png"),
            os.path.join("assets", "buddies", f"{SPECIAL_BUDDY_UUID}.png"),
        ):
            full_path = os.path.join(self.temp_dir.name, relative_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as handle:
                handle.write(b"png")

    def asset_resolver(self, relative_path):
        return os.path.join(self.temp_dir.name, relative_path)

    def test_name_tag_clipboard_and_tracker_fallbacks(self):
        card = build_player_card_display(
            {"game_name": "Neon", "tag": "EU W", "name": "Neon#EU W"},
            resource_path_resolver=self.asset_resolver,
        )

        self.assertEqual(card["displayName"], "Neon#EU W")
        self.assertEqual(card["playerKey"], "Neon#EU W")
        self.assertEqual(card["tagLine"], "#EU W")
        self.assertEqual(card["clipboardName"], "Neon#EU W")
        self.assertEqual(
            card["trackerUrl"],
            "https://tracker.gg/valorant/profile/riot/Neon%23EU%20W",
        )

        fallback = build_player_card_display({}, resource_path_resolver=self.asset_resolver)
        self.assertEqual(fallback["displayName"], "Unknown")
        self.assertEqual(fallback["clipboardName"], "Unknown")

    def test_stat_text_and_tones_use_formatter_thresholds(self):
        card = build_player_card_display(
            {"kd": 1.25, "hs": 40, "wl": "46%", "acs": 224, "rating_change": [-18, 12]},
            resource_path_resolver=self.asset_resolver,
        )

        self.assertEqual(card["kdText"], "1.25")
        self.assertEqual(card["kdTone"], "cyan")
        self.assertEqual(card["hsText"], "40%")
        self.assertEqual(card["hsTone"], "cyan")
        self.assertEqual(card["winRateText"], "46%")
        self.assertEqual(card["winRateTone"], "red")
        self.assertEqual(card["acsText"], "224")
        self.assertEqual(card["acsTone"], "gold")
        self.assertEqual(card["ratingChangeText"], "18")
        self.assertEqual(card["ratingChangeTone"], "negative")
        self.assertEqual(
            [
                {key: change[key] for key in ("text", "valueText", "numericValue", "tone")}
                for change in card["ratingChanges"]
            ],
            [
                {"text": "18", "valueText": "18", "numericValue": -18, "tone": "negative"},
                {"text": "12", "valueText": "12", "numericValue": 12, "tone": "positive"},
            ],
        )

    def test_rank_and_peak_rank_fallback_text_and_icon_paths(self):
        card = build_player_card_display(
            {"rank": "", "peak_rank": "UNRANKED"},
            resource_path_resolver=self.asset_resolver,
        )

        self.assertEqual(card["rankText"], "N/A")
        self.assertEqual(card["rankIconPath"], "")
        self.assertEqual(card["peakRankText"], "N/A")
        self.assertTrue(card["peakRankIconPath"].endswith(os.path.join("assets", "ranks", "Unranked.png")))

        ranked = build_player_card_display(
            {
                "agent": "Jett",
                "level": 24,
                "rank": "Gold 2",
                "peak_rank": "Gold 2",
                "peak_act": "V26A1",
                "matches": 9,
                "rr": 67,
                "skins": {"Vandal": ["Vandal-Skin", "buddy"], "Phantom": "missing-skin"},
            },
            resource_path_resolver=self.asset_resolver,
        )
        self.assertTrue(ranked["agentIconPath"].endswith(os.path.join("assets", "agents", "Jett.png")))
        self.assertTrue(ranked["rankIconPath"].endswith(os.path.join("assets", "ranks", "Gold 2.png")))
        self.assertEqual(ranked["levelText"], "24")
        self.assertEqual(ranked["gamesText"], "9")
        self.assertEqual(ranked["peakActText"], "V26A1")
        self.assertEqual(ranked["rrText"], "67 RR")
        self.assertEqual(ranked["rrProgress"], 67)
        self.assertTrue(ranked["weaponIcons"][0]["iconPath"].endswith(os.path.join("assets", "skins", "vandal-skin.png")))
        self.assertEqual(ranked["weaponIcons"][1]["iconPath"], "")

    def test_flag_buddy_and_party_fields(self):
        formatter = PlayerDisplayFormatter({"p1": {"reason": "Avoid"}})

        card = build_player_card_display(
            {
                "puuid": "p1",
                "skins": {"Vandal": ["skin", {"CharmID": SPECIAL_BUDDY_UUID.upper()}]},
                "party_group_id": "group-1",
            },
            formatter=formatter,
            resource_path_resolver=self.asset_resolver,
        )

        self.assertTrue(card["isFlagged"])
        self.assertEqual(card["flagTooltip"], "Avoid")
        self.assertTrue(card["hasBuddyEquipped"])
        self.assertTrue(card["buddyIconPath"].endswith(os.path.join("assets", "buddies", f"{SPECIAL_BUDDY_UUID}.png")))
        self.assertEqual(card["partyGroupId"], "group-1")

        without_buddy = build_player_card_display(
            {"skins": {"Vandal": ["skin", {"CharmID": "not-the-special-buddy"}]}},
            formatter=formatter,
            resource_path_resolver=self.asset_resolver,
        )

        self.assertFalse(without_buddy["hasBuddyEquipped"])
        self.assertEqual(without_buddy["buddyIconPath"], "")

    def test_player_icon_resolver_fields(self):
        icon_path = os.path.join(self.temp_dir.name, "remote-player.png")

        card = build_player_card_display(
            {"puuid": "p1"},
            resource_path_resolver=self.asset_resolver,
            player_icon_resolver=lambda player: {
                "iconPath": icon_path,
                "tooltip": f"Icon for {player['puuid']}",
            },
        )

        self.assertEqual(card["playerIconPath"], icon_path)
        self.assertEqual(card["playerIconTooltip"], "Icon for p1")

        without_icon = build_player_card_display(
            {"puuid": "p2"},
            resource_path_resolver=self.asset_resolver,
        )

        self.assertEqual(without_icon["playerIconPath"], "")
        self.assertEqual(without_icon["playerIconTooltip"], "")


if __name__ == "__main__":
    unittest.main()
