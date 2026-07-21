import json
import unittest

try:
    from PySide6.QtCore import QCoreApplication
    from frontend.web_bridge import WebFrontendBridge
except Exception:
    QCoreApplication = None
    WebFrontendBridge = None


@unittest.skipIf(WebFrontendBridge is None, "PySide6 is unavailable")
class WebFrontendBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QCoreApplication.instance() or QCoreApplication([])

    def test_dispatch_routes_json_actions_and_refreshes_snapshot(self):
        calls = []
        snapshot_state = {"count": 0}

        def snapshot_factory():
            return dict(snapshot_state)

        def dispatch_callback(action):
            calls.append(action)
            snapshot_state["count"] += 1
            return {"ok": True, "command": action["command"]}

        bridge = WebFrontendBridge(snapshot_factory, dispatch_callback=dispatch_callback)
        result = json.loads(bridge.dispatch(json.dumps({"command": "refresh"})))

        self.assertEqual(result, {"ok": True, "command": "refresh"})
        self.assertEqual(calls, [{"command": "refresh"}])
        self.assertEqual(json.loads(bridge.getSnapshot()), {"count": 1})

    def test_dispatch_reports_invalid_json(self):
        bridge = WebFrontendBridge(lambda: {})
        result = json.loads(bridge.dispatch("{"))

        self.assertFalse(result["ok"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
