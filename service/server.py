"""Minimal BLOOMIN8 pull server for a LAN-only hardware smoke test."""
import hashlib
import secrets
from http.cookies import SimpleCookie
from urllib.request import Request, build_opener, HTTPRedirectHandler
from yuvomi_client import URL as YUVOMI_URL

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None

PREFIX = '/api/extensions/yuvomi-bloomin8'
ORIGIN = os.environ.get('EINK_UI_ORIGIN', '').rstrip('/')

import hmac
import json
import os
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from urllib.parse import parse_qs, urlsplit
import re
from zoneinfo import ZoneInfo

from daily_dashboard import render as render_daily_dashboard
from yuvomi_client import events_for_day
import dashboard_settings
ADMIN_TOKEN = os.environ.get('EINK_SETTINGS_TOKEN', '')

TOKEN = os.environ.get("EINK_PULL_TOKEN", "")
DEVICE_ID = os.environ.get("EINK_DEVICE_ID", "")
PUBLIC_URL = os.environ.get("EINK_PUBLIC_URL", "").rstrip("/")
CLEAN_IMAGE_URL = os.environ.get("EINK_CLEAN_IMAGE_URL", "false").lower() in ("1", "true", "yes")
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
    return render_daily_dashboard(local, events, error, dashboard_settings.load())


def signature(exp):
    return hmac.new(TOKEN.encode(), str(exp).encode(), hashlib.sha256).hexdigest()


def image_url(now):
    # A distinct filename per pull avoids device-side reuse of an old JPEG.
    filename = "dashboard_" + now.strftime("%Y%m%d_%H%M%S") + "_L.jpg"
    path = "/images/" + filename
    if CLEAN_IMAGE_URL:
        return PUBLIC_URL + path
    exp = int((now + timedelta(minutes=15)).timestamp())
    return PUBLIC_URL + path + "?exp=" + str(exp) + "&sig=" + signature(exp)


def valid_image_link(params, now):
    try:
        exp = int(params.get("exp", [""])[0])
        sig = params.get("sig", [""])[0]
        return int(now.timestamp()) <= exp <= int(now.timestamp()) + 3600 and hmac.compare_digest(sig, signature(exp))
    except (ValueError, TypeError):
        return False




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

    def extension(self):
        self.close_connection = True
        path = urlsplit(self.path).path
        if not ORIGIN or not ORIGIN.startswith('https://'):
            return self.json(503, {'error': 'UI origin not configured'})
        cookie = self.headers.get('Cookie', '')
        if not cookie:
            return self.json(401, {'error': 'Session required'})
        try:
            req = Request(YUVOMI_URL.rstrip('/') + '/api/v1/auth/me', headers={'Cookie': cookie, 'Accept': 'application/json'})
            with build_opener(NoRedirect()).open(req, timeout=5) as response:
                identity = json.load(response)
            identity = identity.get('data', identity)
            user = identity.get('user', {})
            permissions = identity.get('permissions', user.get('permissions', {}))
            access = permissions.get('modules', {}).get('ext:yuvomi-bloomin8')
            if access not in ('read', 'write', 'full') or user.get('role') != 'admin':
                return self.json(403, {'error': 'Administrator and module permission required'})
        except Exception:
            return self.json(401, {'error': 'Session verification failed'})
        if self.command == 'GET' and path == PREFIX + '/settings':
            csrf = secrets.token_urlsafe(32)
            data = json.dumps({'settings': dashboard_settings.load(), 'csrf': csrf, 'writable': access in ('write', 'full')}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Set-Cookie', 'b8_csrf=' + csrf + '; Secure; HttpOnly; SameSite=Strict; Path=' + PREFIX + '/')
            self.end_headers()
            self.wfile.write(data)
            return
        if self.command == 'GET' and path == PREFIX + '/preview':
            return self.send_bytes(200, render_image(), 'image/jpeg')
        if self.command == 'PUT' and path == PREFIX + '/settings':
            if access not in ('write', 'full') or self.headers.get('Origin') != ORIGIN:
                return self.json(403, {'error': 'Write denied'})
            try:
                cookies = SimpleCookie(cookie)
                token = cookies['b8_csrf'].value
                if not token or not hmac.compare_digest(token, self.headers.get('X-B8-CSRF', '')):
                    return self.json(403, {'error': 'CSRF denied'})
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 8192:
                    raise ValueError()
                return self.json(200, dashboard_settings.save(json.loads(self.rfile.read(size))))
            except (ValueError, KeyError, TypeError):
                return self.json(400, {'error': 'Invalid settings'})
            except OSError:
                return self.json(500, {'error': 'Storage unavailable'})
        return self.json(404, {'error': 'Not found'})

    def dispatch(self):
        if urlsplit(self.path).path.startswith(PREFIX + '/'):
            return self.extension()

        parsed = urlsplit(self.path)
        params = parse_qs(parsed.query)
        now = datetime.now(timezone.utc)
        if parsed.path == "/dashboard-settings":
            if not self.settings_authorized():
                return self.json(401, {"error": "Unauthorized"})
            return self.json(200, dashboard_settings.load())
        if parsed.path == "/health":
            return self.json(200, {"ok": True})
        if parsed.path == "/diagnostics":
            if not self.authorized():
                return self.json(401, {"error": "Unauthorized"})
            return self.json(200, {"ready": True, "yuvomi_configured": bool(__import__("yuvomi_client").URL and __import__("yuvomi_client").API_TOKEN), "public_url_configured": bool(PUBLIC_URL), "night_pause": sleeping(now), "next_wake": iso(next_wake(now))})
        if re.fullmatch(r"/images/dashboard_\d{8}_\d{6}_L\.jpg", parsed.path) or parsed.path == "/images/dashboard_L.jpg":
            if not CLEAN_IMAGE_URL and not valid_image_link(params, now):
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
            self.log_message("pull action=SHOW image_url=%s next=%s", image_url(now).split("?")[0], iso(next_wake(now)))
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

    def settings_authorized(self):
        return len(ADMIN_TOKEN) >= 24 and hmac.compare_digest(self.headers.get('X-Settings-Token', ''), ADMIN_TOKEN)

    def do_PUT(self):
        self.close_connection = True
        if urlsplit(self.path).path.startswith(PREFIX + '/'):
            return self.extension()
        if urlsplit(self.path).path != '/dashboard-settings':
            return self.json(404, {'error': 'Not found'})
        if not self.settings_authorized():
            return self.json(401, {'error': 'Unauthorized'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 8192:
                raise ValueError('Invalid length')
            data = json.loads(self.rfile.read(size))
            return self.json(200, dashboard_settings.save(data))
        except (ValueError, TypeError):
            return self.json(400, {'error': 'Invalid settings'})
        except OSError:
            return self.json(500, {'error': 'Storage unavailable'})

    def do_GET(self):
        self.dispatch()

    def do_HEAD(self):
        self.dispatch()


if __name__ == "__main__":
    if not TOKEN or len(TOKEN) < 24 or not PUBLIC_URL.startswith(("http://", "https://")):
        raise SystemExit("Set EINK_PULL_TOKEN (>=24 chars) and EINK_PUBLIC_URL")
    ThreadingHTTPServer(("0.0.0.0", 8088), Handler).serve_forever()
