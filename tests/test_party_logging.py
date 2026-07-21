import base64
import json
import tempfile
import unittest

from core.party_tracker import PartyTracker
from core.runtime_logging import initialize_runtime_logging, reset_runtime_logging_for_tests


def encoded_payload(payload):
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


class PartyLoggingTests(unittest.TestCase):
    def tearDown(self):
        reset_runtime_logging_for_tests()

    def test_logs_party_id_detection_from_presence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = initialize_runtime_logging(base_path=tmp_dir)
            tracker = PartyTracker()
            payload = encoded_payload(
                {
                    "partyId": "party-123",
                    "partySize": 2,
                    "queueId": "competitive",
                    "partyState": "MATCHMAKING",
                }
            )

            tracker.feed_chunk(
                7,
                "<presence from='puuid-1@eu1.pvp.net/RC-1'>"
                "<id name='Name' tagline='TAG'/>"
                f"<games><valorant><p>{payload}</p></valorant></games>"
                "</presence>",
            )

            text = log_path.read_text(encoding="utf-8")
            self.assertIn("xmpp_player_party_id_detected", text)
            self.assertIn("party-123", text)
            self.assertIn("puuid-1", text)


if __name__ == "__main__":
    unittest.main()
