import unittest
from types import SimpleNamespace
from unittest.mock import patch


with patch.dict(
    "sys.modules",
    {
        "aiohttp": SimpleNamespace(ClientSession=lambda *args, **kwargs: None),
        "urllib3": SimpleNamespace(
            disable_warnings=lambda *args, **kwargs: None,
            exceptions=SimpleNamespace(InsecureRequestWarning=Warning),
        ),
        "requests": SimpleNamespace(get=lambda *args, **kwargs: None),
    },
):
    from core.api_client import ValoRank


class ValoRankNameFieldTests(unittest.TestCase):
    def setUp(self):
        self.valo_rank = ValoRank.__new__(ValoRank)
        self.valo_rank.frontend_data = {}

    def test_name_service_fields_survive_name_merge(self):
        self.valo_rank.frontend_data["p1"] = {
            "name": "Player#EUW",
            "game_name": "Player",
            "tag": "EUW",
            "name_source": "name_service",
            "xmpp_name_resolved": False,
        }

        fields = self.valo_rank._name_fields_for_puuid("p1", "Jett")

        self.assertEqual(fields["name"], "Player#EUW")
        self.assertEqual(fields["game_name"], "Player")
        self.assertEqual(fields["tag"], "EUW")
        self.assertEqual(fields["name_source"], "name_service")
        self.assertFalse(fields["xmpp_name_resolved"])

    def test_xmpp_fields_survive_name_merge(self):
        self.valo_rank.frontend_data["p1"] = {
            "name": "Xmpp#NA1",
            "game_name": "Xmpp",
            "tag": "NA1",
            "name_source": "xmpp",
            "xmpp_name_resolved": True,
        }

        fields = self.valo_rank._name_fields_for_puuid("p1", "Sova")

        self.assertEqual(fields["name"], "Xmpp#NA1")
        self.assertEqual(fields["game_name"], "Xmpp")
        self.assertEqual(fields["tag"], "NA1")
        self.assertEqual(fields["name_source"], "xmpp")
        self.assertTrue(fields["xmpp_name_resolved"])

    def test_missing_name_fields_fall_back_to_agent_placeholder(self):
        fields = self.valo_rank._name_fields_for_puuid("missing", "Neon")

        self.assertEqual(fields["name"], "Neon")
        self.assertEqual(fields["game_name"], "Neon")
        self.assertEqual(fields["tag"], "")
        self.assertEqual(fields["name_source"], "agent_placeholder")
        self.assertFalse(fields["xmpp_name_resolved"])

    def test_hydration_style_merge_preserves_name_service_fields(self):
        self.valo_rank.frontend_data["p1"] = {
            "name": "Player#EUW",
            "game_name": "Player",
            "tag": "EUW",
            "name_source": "name_service",
            "xmpp_name_resolved": False,
            "agent": "Jett",
        }

        merged = self.valo_rank._merge_player_row("p1", {
            **self.valo_rank._name_fields_for_puuid("p1", "Raze"),
            "agent": "Raze",
            "matches": 5,
            "kd": "1.25",
        })

        self.assertEqual(merged["name"], "Player#EUW")
        self.assertEqual(merged["game_name"], "Player")
        self.assertEqual(merged["tag"], "EUW")
        self.assertEqual(merged["name_source"], "name_service")
        self.assertEqual(merged["agent"], "Raze")
        self.assertEqual(merged["matches"], 5)
        self.assertEqual(merged["kd"], "1.25")


if __name__ == "__main__":
    unittest.main()
