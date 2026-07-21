import base64
import json
import re
import unittest

from core.XMPPMitm import FAKE_PLAYER_JID, XmppMITM, _build_fake_player_presence, _looks_like_tls_record
from core.presence_mode import PRESENCE_MODE_OFFLINE


class XmppMitmTests(unittest.TestCase):
    def test_incoming_roster_injects_fake_player_when_offline(self):
        mitm = XmppMITM(xmpp_port=0, config_mitm=None, log_stream=None)
        mitm.set_presence_mode(PRESENCE_MODE_OFFLINE, broadcast=False)

        roster = (
            "<iq type='result'>"
            "<query xmlns='jabber:iq:riotgames:roster'>"
            "<item jid='friend@ares.pvp.net' />"
            "</query>"
            "</iq>"
        )

        rewritten = mitm._rewrite_incoming_fragment(1, roster)

        self.assertIn(FAKE_PLAYER_JID, rewritten)
        self.assertIn("valscanner-fake-presence", rewritten)
        self.assertIn(1, mitm._fake_player_inserted)
        self.assertIn(1, mitm._fake_player_visible)

    def test_detects_tls_record_bytes_inside_xmpp_stream(self):
        self.assertTrue(_looks_like_tls_record(b"\x16\x03\x01\x00\xca"))
        self.assertFalse(_looks_like_tls_record(b"<presence id='1' />"))

    def test_fake_player_uses_observed_xmpp_domain(self):
        mitm = XmppMITM(xmpp_port=0, config_mitm=None, log_stream=None)
        mitm.set_presence_mode(PRESENCE_MODE_OFFLINE, broadcast=False)
        mitm._observe_xmpp_domain(
            1,
            "<iq id='_xmpp_bind1' type='result'><bind><jid>player@na1.pvp.net/RC-123</jid></bind></iq>",
        )

        roster = (
            "<iq type='result'>"
            "<query xmlns='jabber:iq:riotgames:roster'>"
            "<item jid='friend@na1.pvp.net' />"
            "</query>"
            "</iq>"
        )

        rewritten = mitm._rewrite_incoming_fragment(1, roster)

        self.assertIn("41c322a1-b328-495b-a004-5ccd3e45eae8@na1.pvp.net", rewritten)
        self.assertNotIn("41c322a1-b328-495b-a004-5ccd3e45eae8@ares.pvp.net", rewritten)

    def test_fake_valorant_presence_matches_full_shape_without_deceive_text(self):
        presence = _build_fake_player_presence(version="release-test")
        payload_match = re.search(r"<valorant>.*?<p>(.*?)</p>", presence)
        self.assertIsNotNone(payload_match)

        decoded = base64.b64decode(payload_match.group(1)).decode("utf-8")
        payload = json.loads(decoded)

        self.assertNotIn("Deceive", presence)
        self.assertNotIn("Deceive", decoded)
        self.assertIn("<league_of_legends>", presence)
        self.assertIn("<bacon>", presence)
        self.assertTrue(payload["isValid"])
        self.assertFalse(payload["isIdle"])
        self.assertEqual(payload["partyPresenceData"]["partyClientVersion"], "release-test")
        self.assertEqual(payload["partyPresenceData"]["customGameName"], "ValScanner Active")
        self.assertEqual(payload["premierPresenceData"]["rosterTag"], "ValScanner Active")
        self.assertEqual(payload["playerPresenceData"]["accountLevel"], 999)


if __name__ == "__main__":
    unittest.main()
