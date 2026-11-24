"""Validated, atomic renderer settings. No credentials stored here."""
import json
import os
import tempfile
from pathlib import Path
from threading import RLock

PATH = Path(os.environ.get("EINK_SETTINGS_PATH", "/data/dashboard-settings.json"))
LOCK = RLock()
DEFAULTS = {"showCalendar": True, "showClock": True, "showAllDay": True,
            "calendarLimit": 5, "calendarFontScale": "normal", "imageQuality": 90}
def validate(data):
    if not isinstance(data, dict) or set(data) - set(DEFAULTS):
        raise ValueError("Unsupported settings")
    result = dict(DEFAULTS, **data)
    for key in ("showCalendar", "showClock", "showAllDay"):
        if type(result[key]) is not bool:
            raise ValueError(key)
    for key, lo, hi in (("calendarLimit", 1, 5), ("imageQuality", 50, 95)):
        if type(result[key]) is not int or not lo <= result[key] <= hi:
            raise ValueError(key)
    if result["calendarFontScale"] not in ("compact", "normal", "large"):
        raise ValueError("calendarFontScale")
    return result

def load():
    with LOCK:
        try:
            return validate(json.loads(PATH.read_text()))
        except (OSError, ValueError):
            return DEFAULTS.copy()

def save(data):
    with LOCK:
        result = validate(data)
        PATH.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(dir=PATH.parent)
        try:
            with os.fdopen(fd, "w") as out:
                json.dump(result, out)
                out.flush()
                os.fsync(out.fileno())
            os.replace(name, PATH)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return result
