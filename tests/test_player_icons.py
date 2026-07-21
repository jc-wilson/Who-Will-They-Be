import unittest

from core.player_icons import (
    DEFAULT_PLAYER_ICON_TOOLTIP,
    normalize_player_icon_rules,
)


class PlayerIconRuleTests(unittest.TestCase):
    def test_relative_icon_path_resolves_to_download_host(self):
        rules = normalize_player_icon_rules(
            {
                "abc-123": {
                    "icon": "icons/example.png",
                    "tooltip": "Example",
                }
            }
        )

        self.assertEqual(
            rules,
            {
                "abc-123": {
                    "icon": "https://download.valscanner.com/icons/example.png",
                    "tooltip": "Example",
                }
            },
        )

    def test_full_download_host_url_is_allowed(self):
        rules = normalize_player_icon_rules(
            {
                "abc-123": {
                    "icon": "https://download.valscanner.com/icons/example.webp",
                    "tooltip": "Example",
                }
            }
        )

        self.assertEqual(rules["abc-123"]["icon"], "https://download.valscanner.com/icons/example.webp")

    def test_puuid_is_normalized_case_and_whitespace_insensitively(self):
        rules = normalize_player_icon_rules(
            {
                "  ABC-123  ": {
                    "icon": "icons/example.png",
                    "tooltip": "Example",
                }
            }
        )

        self.assertIn("abc-123", rules)

    def test_invalid_host_is_rejected(self):
        rules = normalize_player_icon_rules(
            {
                "abc-123": {
                    "icon": "https://example.com/icons/example.png",
                    "tooltip": "Example",
                }
            }
        )

        self.assertEqual(rules, {})

    def test_missing_tooltip_uses_default(self):
        rules = normalize_player_icon_rules(
            {
                "abc-123": {
                    "icon": "icons/example.png",
                }
            }
        )

        self.assertEqual(rules["abc-123"]["tooltip"], DEFAULT_PLAYER_ICON_TOOLTIP)

    def test_malformed_entries_are_ignored(self):
        rules = normalize_player_icon_rules(
            {
                "": {"icon": "icons/example.png"},
                "missing-icon": {"tooltip": "No icon"},
                "not-an-object": "icons/example.png",
                "valid": {"icon": "/icons/valid.png"},
            }
        )

        self.assertEqual(
            rules,
            {
                "valid": {
                    "icon": "https://download.valscanner.com/icons/valid.png",
                    "tooltip": DEFAULT_PLAYER_ICON_TOOLTIP,
                }
            },
        )


if __name__ == "__main__":
    unittest.main()
