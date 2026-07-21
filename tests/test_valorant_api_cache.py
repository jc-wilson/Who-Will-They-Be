import json
import os
import tempfile
import unittest
import importlib.util
import sys
import types

try:
    _aiohttp_missing = importlib.util.find_spec("aiohttp") is None
except ValueError:
    _aiohttp_missing = False

if _aiohttp_missing:
    sys.modules["aiohttp"] = types.SimpleNamespace(
        ClientTimeout=lambda **kwargs: types.SimpleNamespace(**kwargs),
    )

from core.valorant_api_cache import (
    VALORANT_API_JSON_MANIFEST,
    refresh_valorant_api_jsons,
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

    async def json(self, **_kwargs):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.urls = []

    def get(self, url, **_kwargs):
        self.urls.append(url)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _json_path(base_path, relative_path):
    return os.path.join(base_path, relative_path)


def _write_json(base_path, relative_path, payload):
    path = _json_path(base_path, relative_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    return path


def _read_json(base_path, relative_path):
    with open(_json_path(base_path, relative_path), "r", encoding="utf-8") as handle:
        return json.load(handle)


class ValorantApiCacheTests(unittest.IsolatedAsyncioTestCase):
    async def test_200_response_overwrites_existing_json_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_entry = VALORANT_API_JSON_MANIFEST[0]
            _write_json(temp_dir, first_entry[1], {"old": True})
            session = FakeSession([FakeResponse(payload={"new": True})])

            results = await refresh_valorant_api_jsons(
                session=session,
                base_path=temp_dir,
                manifest=[first_entry],
            )

            self.assertTrue(results[first_entry[0]])
            self.assertEqual(_read_json(temp_dir, first_entry[1]), {"new": True})

    async def test_non_200_response_preserves_existing_file_contents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_entry = VALORANT_API_JSON_MANIFEST[0]
            _write_json(temp_dir, first_entry[1], {"old": True})
            session = FakeSession([FakeResponse(status=503, payload={"new": True})])

            results = await refresh_valorant_api_jsons(
                session=session,
                base_path=temp_dir,
                manifest=[first_entry],
            )

            self.assertFalse(results[first_entry[0]])
            self.assertEqual(_read_json(temp_dir, first_entry[1]), {"old": True})

    async def test_invalid_json_preserves_existing_file_contents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_entry = VALORANT_API_JSON_MANIFEST[0]
            _write_json(temp_dir, first_entry[1], {"old": True})
            session = FakeSession([FakeResponse(json_error=ValueError("bad json"))])

            results = await refresh_valorant_api_jsons(
                session=session,
                base_path=temp_dir,
                manifest=[first_entry],
            )

            self.assertFalse(results[first_entry[0]])
            self.assertEqual(_read_json(temp_dir, first_entry[1]), {"old": True})

    async def test_missing_file_is_created_only_for_200_response(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_entry, second_entry = VALORANT_API_JSON_MANIFEST[:2]
            session = FakeSession(
                [
                    FakeResponse(payload={"created": True}),
                    FakeResponse(status=500, payload={"not_created": True}),
                ]
            )

            results = await refresh_valorant_api_jsons(
                session=session,
                base_path=temp_dir,
                manifest=[first_entry, second_entry],
            )

            self.assertTrue(results[first_entry[0]])
            self.assertFalse(results[second_entry[0]])
            self.assertEqual(_read_json(temp_dir, first_entry[1]), {"created": True})
            self.assertFalse(os.path.exists(_json_path(temp_dir, second_entry[1])))

    async def test_multiple_endpoint_refreshes_are_independent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first_entry, second_entry, third_entry = VALORANT_API_JSON_MANIFEST[:3]
            _write_json(temp_dir, first_entry[1], {"first": "old"})
            _write_json(temp_dir, second_entry[1], {"second": "old"})
            _write_json(temp_dir, third_entry[1], {"third": "old"})
            session = FakeSession(
                [
                    FakeResponse(payload={"first": "new"}),
                    RuntimeError("down"),
                    FakeResponse(payload={"third": "new"}),
                ]
            )

            results = await refresh_valorant_api_jsons(
                session=session,
                base_path=temp_dir,
                manifest=[first_entry, second_entry, third_entry],
            )

            self.assertTrue(results[first_entry[0]])
            self.assertFalse(results[second_entry[0]])
            self.assertTrue(results[third_entry[0]])
            self.assertEqual(_read_json(temp_dir, first_entry[1]), {"first": "new"})
            self.assertEqual(_read_json(temp_dir, second_entry[1]), {"second": "old"})
            self.assertEqual(_read_json(temp_dir, third_entry[1]), {"third": "new"})


if __name__ == "__main__":
    unittest.main()
