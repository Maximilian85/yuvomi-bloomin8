import importlib.util
import json
import os
import threading
import sys
import unittest
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

os.environ["EINK_PULL_TOKEN"] = "test-secret-long-enough-for-tests"
os.environ["EINK_PUBLIC_URL"] = "http://127.0.0.1:8088"
os.environ["EINK_DEVICE_ID"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "service"))
spec = importlib.util.spec_from_file_location("eink_server", Path(__file__).resolve().parents[1] / "service" / "server.py")
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


class LogicTests(unittest.TestCase):
    def test_jpeg_baseline_landscape_rotation(self):
        from PIL import Image
        img = Image.open(BytesIO(server.render_image()))
        self.assertEqual(img.size, (1200, 1600))
        self.assertEqual(img.mode, "RGB")
        self.assertFalse(img.info.get("progressive", False))

    def test_yuvomi_events_are_rendered(self):
        with patch.object(server, "events_for_day", return_value=([{"title": "Zahnarzt", "start_datetime": "2026-11-16T10:30:00", "assigned_color": "#FF0000"}], None)):
            from PIL import Image
            image = Image.open(BytesIO(server.render_image()))
            self.assertEqual(image.size, (1200, 1600))

    def test_night_pause(self):
        now = datetime(2026, 11, 14, 20, 45, tzinfo=server.TZ)
        wake = server.next_wake(now)
        self.assertEqual(wake.astimezone(server.TZ).hour, 6)
        self.assertEqual(wake.astimezone(server.TZ).day, 15)
        self.assertGreater(wake, now)

    def test_day_interval(self):
        now = datetime(2026, 11, 14, 9, 0, tzinfo=server.TZ)
        self.assertEqual((server.next_wake(now) - now).total_seconds(), 1800)

    def test_signed_link_expiry(self):
        now = datetime.now(timezone.utc)
        from urllib.parse import parse_qs, urlsplit
        params = parse_qs(urlsplit(server.image_url(now)).query)
        self.assertTrue(server.valid_image_link(params, now))
        self.assertFalse(server.valid_image_link(params, now.replace(year=now.year + 1)))
        params["sig"] = ["bad"]
        self.assertFalse(server.valid_image_link(params, now))


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.http.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()

    def request(self, path, token=None, method="GET"):
        headers = {"X-Access-Token": token} if token else {}
        return urlopen(Request(self.base + path, headers=headers, method=method), timeout=5)

    def test_health(self):
        with self.request("/health") as r:
            self.assertEqual(json.load(r), {"ok": True})

    def test_pull_requires_token(self):
        with self.assertRaises(HTTPError) as err:
            self.request("/eink_pull?device_id=abc&pull_id=123")
        self.assertEqual(err.exception.code, 401)

    def test_pull_image_signal(self):
        with patch.object(server, "sleeping", return_value=False):
            with self.request("/eink_pull?device_id=abc&pull_id=unit123&battery=85", server.TOKEN) as r:
                body = json.load(r)
        self.assertEqual(body["status"], 200)
        self.assertEqual(body["type"], "SHOW")
        from urllib.parse import urlsplit
        url = urlsplit(body["data"]["image_url"])
        with self.request(url.path + "?" + url.query) as r:
            jpeg = r.read()
            self.assertEqual(int(r.headers["Content-Length"]), len(jpeg))
            self.assertEqual(r.headers["Content-Type"], "image/jpeg")
            self.assertNotIn("Transfer-Encoding", r.headers)
        with self.request("/eink_signal?pull_id=unit123&success=1", server.TOKEN) as r:
            self.assertEqual(json.load(r)["status"], 200)

    def test_image_without_signature_forbidden(self):
        with self.assertRaises(HTTPError) as err:
            self.request("/images/dashboard_L.jpg")
        self.assertEqual(err.exception.code, 403)

    def test_night_returns_204_in_body(self):
        with patch.object(server, "sleeping", return_value=True), patch.object(server, "next_wake", return_value=datetime.now(timezone.utc) + server.timedelta(minutes=30)):
            with self.request("/eink_pull?device_id=abc&pull_id=night", server.TOKEN) as r:
                self.assertEqual(r.status, 200)
                self.assertEqual(json.load(r)["status"], 204)


if __name__ == "__main__":
    unittest.main()
