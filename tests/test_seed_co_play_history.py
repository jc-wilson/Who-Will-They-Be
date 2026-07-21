import tempfile
import unittest

from core.app_state import default_app_state, load_app_state, save_app_state
from dev_tools.seed_co_play_history import seed_co_play_history


class SeedCoPlayHistoryTests(unittest.TestCase):
    def test_seed_updates_existing_app_state(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            save_app_state(default_app_state(map_uuids=[]), map_uuids=[], base_path=temp_dir)

            seed_co_play_history("self", "other", count=7, match_id="manual", base_path=temp_dir)
            state = load_app_state(map_uuids=[], base_path=temp_dir)

        self.assertEqual(state["co_play_history"]["by_user"]["self"]["counts"]["other"], 7)
        self.assertEqual(state["co_play_history"]["by_user"]["self"]["matches"]["manual"], ["self", "other"])


if __name__ == "__main__":
    unittest.main()
