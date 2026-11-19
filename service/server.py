"""Minimal BLOOMIN8 pull server for a LAN-only hardware smoke test."""
import hashlib
import hmac
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from daily_dashboard import render as render_daily_dashboard
from yuvomi_client import events_for_day

TOKEN = os.environ.get("EINK_PULL_TOKEN", "")
DEVICE_ID = os.environ.get("EINK_DEVICE_ID", "")
PUBLIC_URL = os.environ.get("EINK_PUBLIC_URL", "").rstrip("/")
DEVICE_URL = os.environ.get("EINK_DEVICE_URL", "").rstrip("/")
TZ = ZoneInfo(os.environ.get("TZ", "Europe/Berlin"))
INTERVAL = max(5, int(os.environ.get("EINK_INTERVAL_MINUTES", "30")))
NIGHT_START = int(os.environ.get("EINK_NIGHT_START", "21"))
NIGHT_END = int(os.environ.get("EINK_NIGHT_END", "6"))
_lock = threading.Lock()
_feedback = {}


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sleeping(dt):
    h = dt.astimezone(TZ).hour
    if NIGHT_START == NIGHT_END:
        return False
    if NIGHT_START > NIGHT_END:
        return h >= NIGHT_START or h < NIGHT_END
    return NIGHT_START <= h < NIGHT_END


def next_wake(now):
    local = now.astimezone(TZ)
    candidate = local + timedelta(minutes=INTERVAL)
    # Advance by absolute minutes so DST changes cannot create invalid local times.
    candidate = candidate.astimezone(timezone.utc)
    for _ in range(24 * 60 + 1):
        if not sleeping(candidate):
            return candidate
        candidate += timedelta(minutes=1)
    raise RuntimeError("No valid wake time found")


def render_image(now=None):
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(TZ)
    events, error = events_for_day(local)
    return render_daily_dashboard(local, events, error)


def signature(exp):
    return hmac.new(TOKEN.encode(), str(exp).encode(), hashlib.sha256).hexdigest()


def image_url(now):
    exp = int((now + timedelta(minutes=15)).timestamp())
    return PUBLIC_URL + "/images/dashboard_L.jpg?exp=" + str(exp) + "&sig=" + signature(exp)


def valid_image_link(params, now):
    try:
        exp = int(params.get("exp", [""])[0])
        sig = params.get("sig", [""])[0]
        return int(now.timestamp()) <= exp <= int(now.timestamp()) + 3600 and hmac.compare_digest(sig, signature(exp))
    except (ValueError, TypeError):
        return False



def push_dashboard_to_device():
    """Use the device's documented upload + show APIs as a reliable LAN fallback."""
    jpeg = render_image()
    boundary = "bloomin8-dashboard-upload"
    head = (
        "--" + boundary + "\r\n"
        'Content-Disposition: form-data; name="images"; filename="dashboard_L.jpg"\r\n'
        "Content-Type: image/jpeg\r\n\r\n"
    ).encode("ascii")
    body = head + jpeg + ("\r\n--" + boundary + "--\r\n").encode("ascii")
    upload = Request(
        DEVICE_URL + "/image/uploadMulti?gallery=default&override=1",
        data=body,
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        method="POST",
    )
    with urlopen(upload, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError("Device upload returned HTTP " + str(response.status))
        response.read()
    payload = json.dumps({
        "play_type": 0, "image": "/gallerys/default/dashboard_L.jpg"
    }).encode("utf-8")
    show = Request(
        DEVICE_URL + "/show", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urlopen(show, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError("Device show returned HTTP " + str(response.status))
        response.read()
    print("device push successful bytes=" + str(len(jpeg)), flush=True)


def device_push_loop():
    """Refresh during daytime; keep the existing night pause."""
    import time
    while True:
        now = datetime.now(timezone.utc)
        if not sleeping(now):
            try:
                push_dashboard_to_device()
            except Exception as exc:
                print("device push failed: " + str(exc), flush=True)
        wake = next_wake(datetime.now(timezone.utc))
        time.sleep(max(1, (wake - datetime.now(timezone.utc)).total_seconds()))


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_bytes(self, status, data, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def json(self, status, obj):
        self.send_bytes(status, json.dumps(obj).encode("utf-8"), "application/json")

    def authorized(self):
        return hmac.compare_digest(self.headers.get("X-Access-Token", ""), TOKEN)

    def dispatch(self):
        parsed = urlsplit(self.path)
        params = parse_qs(parsed.query)
        now = datetime.now(timezone.utc)
        if parsed.path == "/health":
            return self.json(200, {"ok": True})
        if parsed.path == "/diagnostics":
            if not self.authorized():
                return self.json(401, {"error": "Unauthorized"})
            return self.json(200, {"ready": True, "yuvomi_configured": bool(__import__("yuvomi_client").URL and __import__("yuvomi_client").API_TOKEN), "public_url_configured": bool(PUBLIC_URL), "night_pause": sleeping(now), "next_wake": iso(next_wake(now))})
        if parsed.path == "/images/dashboard_L.jpg":
            if not valid_image_link(params, now):
                return self.json(403, {"error": "Invalid or expired image link"})
            jpeg = render_image(now)
            self.log_message("image delivered bytes=%d", len(jpeg))
            return self.send_bytes(200, jpeg, "image/jpeg")
        if not self.authorized():
            return self.json(401, {"error": "Unauthorized"})
        if parsed.path == "/eink_pull":
            device = params.get("device_id", [""])[0]
            pull = params.get("pull_id", [""])[0]
            if not device or not pull:
                return self.json(200, {"status": 400, "message": "Missing device_id or pull_id",
                                       "data": {"next_cron_time": iso(next_wake(now))}})
            if DEVICE_ID and not hmac.compare_digest(device, DEVICE_ID):
                return self.json(200, {"status": 403, "message": "Unknown device",
                                       "data": {"next_cron_time": iso(next_wake(now))}})
            with _lock:
                _feedback[pull] = now
                for key, timestamp in list(_feedback.items()):
                    if now - timestamp > timedelta(hours=2):
                        _feedback.pop(key, None)
            self.log_message("pull received battery=%s", params.get("battery", ["?"])[0])
            if sleeping(now):
                self.log_message("pull action=PAUSE next=%s", iso(next_wake(now)))
                return self.json(200, {"status": 204, "message": "Night pause",
                                       "data": {"next_cron_time": iso(next_wake(now))}})
            self.log_message("pull action=SHOW image_path=/images/dashboard_L.jpg next=%s", iso(next_wake(now)))
            return self.json(200, {"status": 200, "type": "SHOW", "message": "Image retrieved successfully",
                                   "data": {"next_cron_time": iso(next_wake(now)),
                                            "image_url": image_url(now)}})
        if parsed.path == "/eink_signal":
            pull = params.get("pull_id", [""])[0]
            with _lock:
                exists = pull in _feedback
                _feedback.pop(pull, None)
            self.log_message("signal success=%s known=%s",
                             params.get("success", ["?"])[0], exists)
            return self.json(200, {"status": 200, "message": "Feedback recorded"})
        return self.json(404, {"error": "Not found"})

    def do_GET(self):
        self.dispatch()

    def do_HEAD(self):
        self.dispatch()


if __name__ == "__main__":
    if not TOKEN or len(TOKEN) < 24 or not PUBLIC_URL.startswith(("http://", "https://")):
        raise SystemExit("Set EINK_PULL_TOKEN (>=24 chars) and EINK_PUBLIC_URL")
    if DEVICE_URL:
        if not DEVICE_URL.startswith(("http://", "https://")):
            raise SystemExit("EINK_DEVICE_URL must start with http:// or https://")
        threading.Thread(target=device_push_loop, daemon=True, name="device-push").start()
    ThreadingHTTPServer(("0.0.0.0", 8088), Handler).serve_forever()
