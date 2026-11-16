"""Read Yuvomi's documented calendar REST API; never access its database."""
import json
import os
import threading
import time
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

URL = os.getenv("YUVOMI_URL", "").rstrip("/")
API_TOKEN = os.getenv("YUVOMI_API_TOKEN", "")
_lock = threading.Lock()
_cache = {"key": None, "until": 0, "events": [], "error": "not configured"}

def events_for_day(local_now):
    day = local_now.strftime("%Y-%m-%d")
    if not URL or not API_TOKEN:
        return [], "Yuvomi-Verbindung nicht konfiguriert"
    with _lock:
        if _cache["key"] == day and _cache["until"] > time.monotonic():
            return list(_cache["events"]), _cache["error"]
    query = urlencode({"from": day, "to": day})
    request = Request(URL + "/api/v1/calendar?" + query, headers={
        "Authorization": "Bearer " + API_TOKEN,
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
        if not isinstance(data.get("data"), list):
            raise ValueError("Unexpected Yuvomi calendar response")
        events = data["data"]
        error = None
    except (HTTPError, URLError, ValueError, TimeoutError, OSError) as exc:
        events, error = [], "Yuvomi-Kalender nicht erreichbar"
        print("Yuvomi calendar fetch failed: " + type(exc).__name__, flush=True)
    with _lock:
        _cache.update(key=day, until=time.monotonic() + (60 if error is None else 15),
                      events=events, error=error)
    return list(events), error
