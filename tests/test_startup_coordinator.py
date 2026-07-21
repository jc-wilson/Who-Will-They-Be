import unittest
import importlib.util
import sys
import types


def is_missing_module(module_name):
    if module_name in sys.modules:
        return False
    try:
        return importlib.util.find_spec(module_name) is None
    except ValueError:
        return False


if is_missing_module("aiohttp"):
    sys.modules["aiohttp"] = types.SimpleNamespace(
        ClientTimeout=lambda **kwargs: types.SimpleNamespace(**kwargs),
    )

if is_missing_module("requests"):
    sys.modules["requests"] = types.SimpleNamespace()

if is_missing_module("urllib3"):
    sys.modules["urllib3"] = types.SimpleNamespace(
        disable_warnings=lambda *_args, **_kwargs: None,
        exceptions=types.SimpleNamespace(InsecureRequestWarning=Warning),
    )

from core.startup_coordinator import AppStartupCoordinator


class FakeMitmService:
    def __init__(self):
        self.start_calls = 0
        self.stop_calls = 0
        self.restart_calls = 0
        self.ensure_riot_started_calls = 0

    def can_reuse_active_session(self):
        return False

    async def start(self):
        self.start_calls += 1

    async def stop(self):
        self.stop_calls += 1

    async def restart_riot_client(self):
        self.restart_calls += 1

    async def ensure_riot_started(self):
        self.ensure_riot_started_calls += 1
        return True

    def mark_background_hold(self, _enabled):
        return None


class StartupCoordinatorForcedDisabledTests(unittest.IsolatedAsyncioTestCase):
    def make_coordinator(self):
        coordinator = AppStartupCoordinator()
        coordinator.mitm_service = FakeMitmService()
        return coordinator

    async def test_initialize_does_not_start_mitm_when_forced_disabled(self):
        coordinator = self.make_coordinator()
        await coordinator.disable_party_detection_for_session()

        started = await coordinator.initialize()

        self.assertFalse(started)
        self.assertFalse(coordinator.party_detection_enabled)
        self.assertFalse(coordinator.restart_required)
        self.assertEqual(coordinator.last_status, "Party detection disabled for this session.")
        self.assertEqual(coordinator.mitm_service.start_calls, 0)
        self.assertEqual(coordinator.mitm_service.ensure_riot_started_calls, 0)

    async def test_ensure_riot_with_mitm_is_noop_when_forced_disabled(self):
        coordinator = self.make_coordinator()
        await coordinator.disable_party_detection_for_session()

        started = await coordinator.ensure_riot_with_mitm()

        self.assertFalse(started)
        self.assertFalse(coordinator.party_detection_enabled)
        self.assertEqual(coordinator.mitm_service.start_calls, 0)
        self.assertEqual(coordinator.mitm_service.ensure_riot_started_calls, 0)

    async def test_restart_riot_client_is_noop_when_forced_disabled(self):
        coordinator = self.make_coordinator()
        await coordinator.disable_party_detection_for_session()

        restarted = await coordinator.restart_riot_client()

        self.assertFalse(restarted)
        self.assertFalse(coordinator.party_detection_enabled)
        self.assertEqual(coordinator.mitm_service.start_calls, 0)
        self.assertEqual(coordinator.mitm_service.restart_calls, 0)


if __name__ == "__main__":
    unittest.main()
