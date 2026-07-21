import unittest

from core.co_play_history import (
    annotate_frontend_data_with_co_play_counts,
    apply_live_match_co_play_history,
    get_all_account_counts,
    record_live_match_co_play,
)


def players(count):
    return [{"Subject": f"p{i}"} for i in range(count)]


class CoPlayHistoryTests(unittest.TestCase):
    def test_live_ten_player_match_records_all_puuids(self):
        history = {"by_user": {}}

        recorded = apply_live_match_co_play_history(
            {"p1": {"puuid": "p1"}},
            history,
            "p0",
            "match-1",
            {"Players": players(10)},
        )

        self.assertTrue(recorded)
        user_history = history["by_user"]["p0"]
        self.assertEqual(user_history["matches"]["match-1"], [f"p{i}" for i in range(10)])
        self.assertNotIn("p0", user_history["counts"])
        self.assertEqual(user_history["counts"]["p1"], 1)

    def test_pregame_data_does_not_record(self):
        history = {"by_user": {}}

        recorded = apply_live_match_co_play_history({}, history, "p0", "match-1", None)

        self.assertFalse(recorded)
        self.assertNotIn("p0", history["by_user"])

    def test_non_ten_unique_players_do_not_record(self):
        for participant_count in (9, 11):
            history = {"by_user": {}}

            recorded = apply_live_match_co_play_history(
                {},
                history,
                "p0",
                f"match-{participant_count}",
                {"Players": players(participant_count)},
            )

            self.assertFalse(recorded)

    def test_duplicate_match_does_not_increment_twice(self):
        history = {"by_user": {}}
        participants = [f"p{i}" for i in range(10)]

        self.assertTrue(record_live_match_co_play(history, "p0", "match-1", participants))
        self.assertFalse(record_live_match_co_play(history, "p0", "match-1", participants))

        self.assertEqual(history["by_user"]["p0"]["counts"]["p1"], 1)

    def test_previous_only_annotation_uses_old_count_before_recording_current_match(self):
        history = {
            "by_user": {
                "p0": {
                    "matches": {"old": ["p0", "p1"]},
                    "counts": {"p1": 1},
                }
            }
        }
        frontend_data = {"p1": {"puuid": "p1"}, "p2": {"puuid": "p2"}}

        recorded = apply_live_match_co_play_history(
            frontend_data,
            history,
            "p0",
            "new",
            {"Players": players(10)},
        )

        self.assertTrue(recorded)
        self.assertEqual(frontend_data["p1"]["co_play_count"], 1)
        self.assertEqual(frontend_data["p2"]["co_play_count"], 0)
        self.assertEqual(history["by_user"]["p0"]["counts"]["p1"], 2)

    def test_local_user_is_not_counted_as_own_coplayer(self):
        history = {"by_user": {}}

        record_live_match_co_play(history, "p0", "match-1", [f"p{i}" for i in range(10)])

        self.assertNotIn("p0", history["by_user"]["p0"]["counts"])

    def test_annotation_without_recording_for_existing_counts(self):
        history = {"by_user": {"p0": {"matches": {}, "counts": {"p1": 3}}}}
        frontend_data = {"p1": {"puuid": "p1"}}

        annotate_frontend_data_with_co_play_counts(frontend_data, history, "p0")

        self.assertEqual(frontend_data["p1"]["co_play_count"], 3)

    def test_annotation_sums_counts_across_all_local_accounts(self):
        history = {
            "by_user": {
                "main": {"matches": {}, "counts": {"shared": 2, "main": 9}},
                "alt": {"matches": {}, "counts": {"shared": 4}},
            }
        }
        frontend_data = {"shared": {"puuid": "shared"}}

        annotate_frontend_data_with_co_play_counts(frontend_data, history, "alt")

        self.assertEqual(frontend_data["shared"]["co_play_count"], 6)

    def test_all_account_counts_ignores_malformed_entries(self):
        history = {
            "by_user": {
                "main": {"counts": {"p1": "2", "p2": "bad", "p3": 0}},
                "bad": "not-a-dict",
            }
        }

        self.assertEqual(get_all_account_counts(history), {"p1": 2})


if __name__ == "__main__":
    unittest.main()
