import unittest
import importlib.util
import sys
import types

if importlib.util.find_spec("aiohttp") is None:
    sys.modules["aiohttp"] = types.SimpleNamespace(
        ClientTimeout=lambda **kwargs: types.SimpleNamespace(**kwargs),
    )

from core.remote_policy import (
    DEFAULT_BAN_REASON,
    DEFAULT_KILLSWITCH_REASON,
    check_banlist,
    check_killswitch,
    check_xmpp_killswitch,
    parse_banlist_policy,
    parse_killswitch_policy,
)


class FakeResponse:
    def __init__(self, status=200, payload=None, json_error=None):
        self.status = status
        self.payload = payload
        self.json_error = json_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False

    async def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    def get(self, *_args, **_kwargs):
        if self.error is not None:
            raise self.error
        return self.response


class RemotePolicyParserTests(unittest.TestCase):
    def test_killswitch_on_blocks_case_insensitively_with_reason(self):
        decision = parse_killswitch_policy({"killswitch": " ON ", "reason": "maintenance"})

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, "maintenance")

    def test_killswitch_on_uses_default_reason(self):
        decision = parse_killswitch_policy({"killswitch": "on"})

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, DEFAULT_KILLSWITCH_REASON)

    def test_killswitch_off_missing_or_invalid_allows(self):
        self.assertFalse(parse_killswitch_policy({"killswitch": "off"}).blocked)
        self.assertFalse(parse_killswitch_policy({}).blocked)
        self.assertFalse(parse_killswitch_policy([]).blocked)

    def test_banlist_array_matches_case_and_whitespace_insensitively(self):
        decision = parse_banlist_policy(
            [{"puuid": "  ABC-123  ", "reason": "banned"}],
            "abc-123",
        )

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, "banned")

    def test_banlist_single_object_is_supported(self):
        decision = parse_banlist_policy({"puuid": "abc-123"}, " ABC-123 ")

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, DEFAULT_BAN_REASON)

    def test_banlist_empty_malformed_or_nonmatching_allows(self):
        self.assertFalse(parse_banlist_policy([], "abc").blocked)
        self.assertFalse(parse_banlist_policy([None, {"reason": "missing puuid"}], "abc").blocked)
        self.assertFalse(parse_banlist_policy([{"puuid": "other"}], "abc").blocked)


class RemotePolicyFetchTests(unittest.IsolatedAsyncioTestCase):
    async def test_killswitch_network_failure_allows(self):
        decision = await check_killswitch(session=FakeSession(error=RuntimeError("down")))

        self.assertFalse(decision.blocked)
        self.assertFalse(decision.checked)

    async def test_killswitch_invalid_json_allows(self):
        decision = await check_killswitch(
            session=FakeSession(response=FakeResponse(status=200, json_error=ValueError("bad json")))
        )

        self.assertFalse(decision.blocked)
        self.assertFalse(decision.checked)

    async def test_killswitch_active_blocks_with_reason(self):
        decision = await check_killswitch(
            session=FakeSession(response=FakeResponse(payload={"killswitch": "on", "reason": "closed"}))
        )

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, "closed")

    async def test_xmpp_killswitch_active_blocks_with_reason(self):
        decision = await check_xmpp_killswitch(
            session=FakeSession(response=FakeResponse(payload={"killswitch": "on", "reason": "xmpp disabled"}))
        )

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, "xmpp disabled")

    async def test_xmpp_killswitch_off_allows(self):
        decision = await check_xmpp_killswitch(
            session=FakeSession(response=FakeResponse(payload={"killswitch": "off"}))
        )

        self.assertFalse(decision.blocked)
        self.assertTrue(decision.checked)

    async def test_xmpp_killswitch_network_failure_allows(self):
        decision = await check_xmpp_killswitch(session=FakeSession(error=RuntimeError("down")))

        self.assertFalse(decision.blocked)
        self.assertFalse(decision.checked)

    async def test_xmpp_killswitch_http_failure_allows(self):
        decision = await check_xmpp_killswitch(session=FakeSession(response=FakeResponse(status=503)))

        self.assertFalse(decision.blocked)
        self.assertFalse(decision.checked)

    async def test_xmpp_killswitch_invalid_json_allows(self):
        decision = await check_xmpp_killswitch(
            session=FakeSession(response=FakeResponse(status=200, json_error=ValueError("bad json")))
        )

        self.assertFalse(decision.blocked)
        self.assertFalse(decision.checked)

    async def test_banlist_http_failure_allows(self):
        decision = await check_banlist("abc", session=FakeSession(response=FakeResponse(status=503)))

        self.assertFalse(decision.blocked)
        self.assertFalse(decision.checked)

    async def test_banlist_matching_entry_blocks_with_reason(self):
        decision = await check_banlist(
            "abc",
            session=FakeSession(response=FakeResponse(payload=[{"puuid": "ABC", "reason": "nope"}])),
        )

        self.assertTrue(decision.blocked)
        self.assertEqual(decision.reason, "nope")

    async def test_banlist_nonmatching_entry_allows(self):
        decision = await check_banlist(
            "abc",
            session=FakeSession(response=FakeResponse(payload=[{"puuid": "other"}])),
        )

        self.assertFalse(decision.blocked)
        self.assertTrue(decision.checked)


if __name__ == "__main__":
    unittest.main()
