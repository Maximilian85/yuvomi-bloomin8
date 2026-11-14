import importlib.util
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("EINK_PULL_TOKEN", "test-secret")
os.environ.setdefault("EINK_DEVICE_ID", "test-device")
os.environ.setdefault("EINK_PUBLIC_URL", "http://localhost:8088")
spec = importlib.util.spec_from_file_location("eink_server", Path(__file__).resolve().parents[1] / "service" / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class ServerTests(unittest.TestCase):
    def test_baseline_jpeg_dimensions(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(server, "OUT", Path(tmp)):
                path = server.make_image()
                with Image.open(path) as img:
                    self.assertEqual(img.size, (1200, 1600))
                    self.assertEqual(img.mode, "RGB")
                    self.assertEqual(img.info.get("progressive"), None)

    def test_next_wake_is_future(self):
        now = datetime(2026, 11, 14, 20, 45, tzinfo=server.TZ)
        result = server.next_wake(now)
        self.assertGreater(result, now)
        self.assertEqual(result.hour, 6)

    def test_iso_utc(self):
        self.assertEqual(server.iso(datetime(2026, 1, 1, 12, tzinfo=timezone.utc)), "2026-01-01T12:00:00Z")


if __name__ == "__main__":
    unittest.main()
