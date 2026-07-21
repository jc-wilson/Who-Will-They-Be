import importlib.util
import base64
import json
import sys
import types
import unittest
from unittest.mock import patch

if importlib.util.find_spec("requests") is None:
    sys.modules["requests"] = types.SimpleNamespace(RequestException=Exception)

if importlib.util.find_spec("urllib3") is None:
    sys.modules["urllib3"] = types.SimpleNamespace(
        disable_warnings=lambda *_args, **_kwargs: None,
        exceptions=types.SimpleNamespace(InsecureRequestWarning=Warning),
    )

from core.ConfigMITM import ConfigMITM
from core.SharedValues import localhostChatHost


class ConfigMitmTests(unittest.TestCase):
    def test_patch_client_config_uses_valid_localhost_certificate_host(self):
        mitm = ConfigMITM(host="127.0.0.1", http_port=0, xmpp_port=35478)
        self.addCleanup(mitm.server.server_close)

        data = {
            "chat.host": "upstream.chat.riotgames.com",
            "chat.port": 5223,
            "chat.affinities": {
                "eu": "eu.chat.riotgames.com",
                "na": "na.chat.riotgames.com",
            },
            "chat.allow_bad_cert.enabled": False,
            "chat.use_tls.enabled": True,
        }

        patched = mitm.patch_client_config(data)

        self.assertEqual(patched["chat.host"], localhostChatHost)
        self.assertEqual(patched["chat.port"], 35478)
        self.assertEqual(set(patched["chat.affinities"].values()), {localhostChatHost})
        self.assertFalse(patched["chat.allow_bad_cert.enabled"])
        self.assertTrue(patched["chat.use_tls.enabled"])
        self.assertEqual(mitm.get_upstream_chat_endpoint(), ("upstream.chat.riotgames.com", 5223))

    def test_patch_client_config_falls_back_to_first_affinity_without_chat_host(self):
        mitm = ConfigMITM(host="127.0.0.1", http_port=0, xmpp_port=35478)
        self.addCleanup(mitm.server.server_close)

        mitm.patch_client_config({
            "chat.port": 5223,
            "chat.affinities": {
                "eu": "eu.chat.riotgames.com",
                "na": "na.chat.riotgames.com",
            },
        })

        self.assertEqual(mitm.get_upstream_chat_endpoint(), ("eu.chat.riotgames.com", 5223))

    def test_patch_client_config_uses_player_affinity_when_enabled(self):
        mitm = ConfigMITM(host="127.0.0.1", http_port=0, xmpp_port=35478)
        self.addCleanup(mitm.server.server_close)

        payload = base64.urlsafe_b64encode(json.dumps({"affinity": "na"}).encode("utf-8")).decode("utf-8").rstrip("=")
        fake_jwt = f"header.{payload}.signature"

        class FakeResponse:
            text = fake_jwt

            def raise_for_status(self):
                return None

        with patch("core.ConfigMITM.requests.get", return_value=FakeResponse(), create=True):
            mitm.patch_client_config(
                {
                    "chat.host": "fallback.chat.riotgames.com",
                    "chat.port": 5223,
                    "chat.affinity.enabled": True,
                    "chat.affinities": {
                        "eu": "eu.chat.riotgames.com",
                        "na": "na.chat.riotgames.com",
                    },
                },
                headers={"Authorization": "Bearer token"},
            )

        self.assertEqual(mitm.get_upstream_chat_endpoint(), ("na.chat.riotgames.com", 5223))


if __name__ == "__main__":
    unittest.main()
