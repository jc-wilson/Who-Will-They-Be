import tempfile
import unittest
from unittest import mock
from pathlib import Path

from core.mitm import InMemoryLogStream, RiotMitmService
from core.runtime_logging import initialize_runtime_logging, reset_runtime_logging_for_tests


class XmppLogStreamTests(unittest.IsolatedAsyncioTestCase):
    def tearDown(self):
        reset_runtime_logging_for_tests()

    async def test_writes_entries_to_file_and_memory(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "xmpp.jsonl"
            stream = InMemoryLogStream(log_path=log_path)

            await stream.write('{"type":"start"}\n')
            await stream.write('{"type":"event"}')
            await stream.flush()
            await stream.close()

            self.assertEqual(
                log_path.read_text(encoding="utf-8"),
                '{"type":"start"}\n{"type":"event"}\n',
            )
            self.assertEqual(stream.entries, ['{"type":"start"}\n', '{"type":"event"}'])

    async def test_default_log_path_is_enabled_in_frozen_builds(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = initialize_runtime_logging(base_path=tmp_dir)
            with mock.patch("core.mitm.sys.frozen", True, create=True):
                service = RiotMitmService()

        self.assertEqual(service.xmpp_log_path, log_path)

    async def test_default_log_path_uses_runtime_launch_log_in_dev_runs(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = initialize_runtime_logging(base_path=tmp_dir)
            service = RiotMitmService()

        self.assertEqual(service.xmpp_log_path, log_path)

    async def test_explicit_log_path_is_honored_in_frozen_builds(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "xmpp.jsonl"
            with mock.patch("core.mitm.sys.frozen", True, create=True):
                service = RiotMitmService(xmpp_log_path=log_path)

            self.assertEqual(service.xmpp_log_path, log_path)


if __name__ == "__main__":
    unittest.main()
