import unittest
import tempfile

from core.app_state import APP_STATE_VERSION, default_app_state, load_app_state, normalize_app_state, save_app_state


class AppStateCoPlayHistoryTests(unittest.TestCase):
    def test_default_state_includes_empty_co_play_history(self):
        state = default_app_state(map_uuids=[])

        self.assertEqual(state["version"], APP_STATE_VERSION)
        self.assertEqual(state["co_play_history"], {"by_user": {}})
        self.assertEqual(state["theme_surface_mode"], "transparent")

    def test_normalize_missing_or_malformed_co_play_history(self):
        self.assertEqual(
            normalize_app_state({"co_play_history": "bad"}, map_uuids=[])["co_play_history"],
            {"by_user": {}},
        )
        self.assertEqual(
            normalize_app_state({}, map_uuids=[])["co_play_history"],
            {"by_user": {}},
        )

    def test_save_load_round_trip_preserves_co_play_history(self):
        state = default_app_state(map_uuids=[])
        state["co_play_history"] = {
            "by_user": {
                "self": {
                    "matches": {"match-1": ["self", "other"]},
                    "counts": {"other": 1},
                }
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            save_app_state(state, map_uuids=[], base_path=temp_dir)
            loaded = load_app_state(map_uuids=[], base_path=temp_dir)

        self.assertEqual(loaded["co_play_history"], state["co_play_history"])


class AppStateThemeSurfaceModeTests(unittest.TestCase):
    def test_normalize_missing_theme_surface_mode_defaults_to_transparent(self):
        self.assertEqual(
            normalize_app_state({}, map_uuids=[])["theme_surface_mode"],
            "transparent",
        )

    def test_normalize_invalid_theme_surface_mode_defaults_to_transparent(self):
        self.assertEqual(
            normalize_app_state({"theme_surface_mode": "mist"}, map_uuids=[])["theme_surface_mode"],
            "transparent",
        )

    def test_normalize_valid_theme_surface_modes(self):
        self.assertEqual(
            normalize_app_state({"theme_surface_mode": "transparent"}, map_uuids=[])["theme_surface_mode"],
            "transparent",
        )
        self.assertEqual(
            normalize_app_state({"theme_surface_mode": "opaque"}, map_uuids=[])["theme_surface_mode"],
            "opaque",
        )

    def test_save_load_round_trip_preserves_theme_surface_mode(self):
        state = default_app_state(map_uuids=[])
        state["theme_surface_mode"] = "opaque"

        with tempfile.TemporaryDirectory() as temp_dir:
            save_app_state(state, map_uuids=[], base_path=temp_dir)
            loaded = load_app_state(map_uuids=[], base_path=temp_dir)

        self.assertEqual(loaded["theme_surface_mode"], "opaque")


if __name__ == "__main__":
    unittest.main()
