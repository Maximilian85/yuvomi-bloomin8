import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

TOKEN = os.environ.get("EINK_PULL_TOKEN", "")
DEVICE_ID = os.environ.get("EINK_DEVICE_ID", "")
PUBLIC_URL = os.environ.get("EINK_PUBLIC_URL", "").rstrip("/")
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Berlin"))
INTERVAL = max(5, int(os.environ.get("EINK_INTERVAL_MINUTES", "30")))
NIGHT_START = int(os.environ.get("EINK_NIGHT_START", "21"))
NIGHT_END = int(os.environ.get("EINK_NIGHT_END", "6"))
OUT = Path("/app/data")
OUT.mkdir(parents=True, exist_ok=True)
pulls = {}


def iso(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def next_wake(now):
    candidate = now.astimezone(TZ) + timedelta(minutes=INTERVAL)
    for _ in range(1440):
        hour = candidate.hour
        sleeping = (NIGHT_START <= hour or hour < NIGHT_END) if NIGHT_START > NIGHT_END else (NIGHT_START <= hour < NIGHT_END)
        if not sleeping:
            return candidate
        candidate += timedelta(minutes=1)
    return now + timedelta(hours=24)


def make_image():
    # Firmware expects portrait pixel storage even for landscape display.
    im = Image.new("RGB", (1600, 1200), "#faf8f0")
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 58)
        small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
        small = font
    d.text((100, 140), "Yuvomi BLOOMIN8", font=font, fill="#283c48")
    d.text((100, 260), "Verbindungstest", font=font, fill="#283c48")
    d.text((100, 380), datetime.now(TZ).strftime("%d.%m.%Y %H:%M"), font=small, fill="#536772")
    d.text((100, 500), "Kalender, Wetter und Immich folgen.", font=small, fill="#536772")
    # Landscape: clockwise rotation of content into portrait storage.
    im = im.rotate(270, expand=True)
    # Store landscape content as portrait pixels as required by firmware.
    path = OUT / "dashboard_L.jpg"
    im.save(path, "JPEG", quality=88, progressive=False, subsampling=0)
    return path


class Handler(BaseHTTPRequestHandler):
    def send_bytes(self, code, data, mime):
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def reply(self, code, obj):
        self.send_bytes(code, json.dumps(obj).encode(), "application/json")

    def authorized(self):
        return bool(TOKEN) and hmac.compare_digest(self.headers.get("X-Access-Token", ""), TOKEN)

    def handle_request(self):
        path = urlsplit(self.path)
        args = parse_qs(path.query)
        if path.path == "/health":
            return self.reply(200, {"ok": True})
        if path.path == "/images/dashboard_L.jpg" and hmac.compare_digest(args.get("token", [""])[0], TOKEN) and TOKEN:\n            image = OUT / "dashboard_L.jpg"\n            if not image.exists():\n                make_image()\n            return self.send_bytes(200, image.read_bytes(), "image/jpeg")\n        if not self.authorized():
            return self.reply(401, {"status": 401, "message": "Unauthorized"})
        if path.path == "/eink_pull":
            device = args.get("device_id", [""])[0]
            pull = args.get("pull_id", [""])[0]
            if not device or not pull or not DEVICE_ID or not hmac.compare_digest(device, DEVICE_ID):
                return self.reply(400, {"status": 400, "message": "Unknown device or missing pull_id"})
            now = datetime.now(timezone.utc)
            pulls[pull] = (device, now)
            for key, (_, when) in list(pulls.items()):
                if now - when > timedelta(hours=2):
                    pulls.pop(key, None)
            make_image()
            return self.reply(200, {
                "status": 200, "type": "SHOW", "message": "Image available",
                "data": {"next_cron_time": iso(next_wake(now)),
                         "image_url": PUBLIC_URL + "/images/dashboard_L.jpg?token=" + TOKEN}
            })
        if path.path == "/eink_signal":
            pull = args.get("pull_id", [""])[0]
            if pull not in pulls:
                return self.reply(404, {"status": 404, "message": "Unknown pull_id"})
            pulls.pop(pull, None)
            return self.reply(200, {"status": 200, "message": "Feedback recorded"})
        if path.path == "/images/dashboard_L.jpg":
            image = OUT / "dashboard_L.jpg"
            if not image.exists():
                make_image()
            return self.send_bytes(200, image.read_bytes(), "image/jpeg")
        return self.reply(404, {"status": 404})

    def do_GET(self):
        self.handle_request()

    def do_HEAD(self):
        self.handle_request()


if __name__ == "__main__":
    if not TOKEN or not DEVICE_ID or not PUBLIC_URL.startswith(("http://", "https://")):
        raise SystemExit("Configure EINK_PULL_TOKEN, EINK_DEVICE_ID and EINK_PUBLIC_URL")
    ThreadingHTTPServer(("0.0.0.0", 8088), Handler).serve_forever()
