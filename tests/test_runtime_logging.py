import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import runtime_logging


class RuntimeLoggingTests(unittest.TestCase):
    def tearDown(self):
        runtime_logging.reset_runtime_logging_for_tests()

    def test_initializes_launch_log_and_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = runtime_logging.initialize_runtime_logging(base_path=tmp_dir, app_version="test")
            runtime_logging.log_event("xmpp_socket_open", url="https://example.test/path?token=secret&ok=1")

            self.assertEqual(log_path.parent, Path(tmp_dir) / "logs")
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

            self.assertEqual(records[0]["event"], "runtime_log_started")
            self.assertEqual(records[1]["event"], "xmpp_socket_open")
            self.assertEqual(records[1]["url"], "https://example.test/path?token=%5BREDACTED%5D&ok=1")

    def test_non_xmpp_events_are_not_written(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = runtime_logging.initialize_runtime_logging(base_path=tmp_dir)
            runtime_logging.log_event("api_response", url="https://example.test")

            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([record["event"] for record in records], ["runtime_log_started"])

    def test_retention_keeps_latest_three_launch_logs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            logs_dir = Path(tmp_dir) / "logs"
            logs_dir.mkdir()
            for index in range(5):
                old_log = logs_dir / f"valscanner_20260101_00000{index}.jsonl"
                old_log.write_text("{}\n", encoding="utf-8")

            current = runtime_logging.initialize_runtime_logging(base_path=tmp_dir, max_log_files=3)
            remaining = sorted(logs_dir.glob("valscanner_*.jsonl"))

            self.assertEqual(len(remaining), 3)
            self.assertIn(current, remaining)

    def test_redacts_headers_and_auth_strings(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = runtime_logging.initialize_runtime_logging(base_path=tmp_dir)
            runtime_logging.log_event(
                "xmpp_secret_test",
                headers={
                    "Authorization": "Bearer abc.def.ghi",
                    "X-Riot-Entitlements-JWT": "secret",
                },
                message="using Basic dXNlcjpwYXNz and Bearer rawtoken",
            )

            text = log_path.read_text(encoding="utf-8")
            self.assertNotIn("abc.def.ghi", text)
            self.assertNotIn("dXNlcjpwYXNz", text)
            self.assertNotIn("rawtoken", text)
            self.assertIn("[REDACTED]", text)

    def test_frozen_root_uses_executable_directory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_exe = str(Path(tmp_dir) / "ValScanner.exe")
            with mock.patch("core.runtime_logging.sys.frozen", True, create=True), mock.patch(
                "core.runtime_logging.sys.executable",
                fake_exe,
            ):
                self.assertEqual(runtime_logging.get_logs_dir(), Path(tmp_dir) / "logs")


if __name__ == "__main__":
    unittest.main()
