import unittest

from core.delayed_hydration import should_run_delayed_hydration


class DelayedHydrationGateTests(unittest.TestCase):
    def make_state(self):
        return {
            "match_id": "match-1",
            "hydration_match_id": "match-1",
            "last_match_id": "match-1",
            "hydrated_match_ids": set(),
            "delay_ready_match_ids": set(),
            "coregame_ready_match_ids": set(),
            "running_match_ids": set(),
        }

    def should_run(self, **overrides):
        state = self.make_state()
        state.update(overrides)
        return should_run_delayed_hydration(**state)

    def test_delay_first_waits_for_coregame(self):
        self.assertFalse(
            self.should_run(delay_ready_match_ids={"match-1"})
        )
        self.assertTrue(
            self.should_run(
                delay_ready_match_ids={"match-1"},
                coregame_ready_match_ids={"match-1"},
            )
        )

    def test_coregame_first_waits_for_delay(self):
        self.assertFalse(
            self.should_run(coregame_ready_match_ids={"match-1"})
        )
        self.assertTrue(
            self.should_run(
                delay_ready_match_ids={"match-1"},
                coregame_ready_match_ids={"match-1"},
            )
        )

    def test_both_conditions_true_hydrates(self):
        self.assertTrue(
            self.should_run(
                delay_ready_match_ids={"match-1"},
                coregame_ready_match_ids={"match-1"},
            )
        )

    def test_wrong_or_stale_match_id_does_not_hydrate(self):
        ready = {
            "delay_ready_match_ids": {"match-1"},
            "coregame_ready_match_ids": {"match-1"},
        }
        self.assertFalse(self.should_run(hydration_match_id="match-2", **ready))
        self.assertFalse(self.should_run(last_match_id="match-2", **ready))
        self.assertFalse(self.should_run(match_id="match-2", **ready))

    def test_already_hydrated_match_id_does_not_hydrate_again(self):
        self.assertFalse(
            self.should_run(
                hydrated_match_ids={"match-1"},
                delay_ready_match_ids={"match-1"},
                coregame_ready_match_ids={"match-1"},
            )
        )

    def test_running_hydration_guard_prevents_duplicate(self):
        self.assertFalse(
            self.should_run(
                delay_ready_match_ids={"match-1"},
                coregame_ready_match_ids={"match-1"},
                running_match_ids={"match-1"},
            )
        )


if __name__ == "__main__":
    unittest.main()
