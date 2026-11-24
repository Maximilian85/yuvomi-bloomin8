"""1600x1200 daily family dashboard; rotated to BLOOMIN8 portrait JPEG."""
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1200
INK, MUTED, BG, LINE = "#18262C", "#45535A", "#FAFAF7", "#BAC3C3"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size)

def text(draw, xy, value, size, bold=False, fill=INK):
    draw.text(xy, str(value), font=font(size, bold), fill=fill)

def fit(draw, value, max_width, size, bold=False):
    value = str(value or "").replace("\n", " ").strip()
    if draw.textlength(value, font=font(size, bold)) <= max_width:
        return value
    while value and draw.textlength(value + "…", font=font(size, bold)) > max_width:
        value = value[:-1]
    return value + "…"

def panel(draw, xy, title):
    draw.rounded_rectangle(xy, radius=20, fill="#FFFFFF", outline=LINE, width=3)
    text(draw, (xy[0]+30, xy[1]+22), title, 42, True)
    draw.line((xy[0]+30, xy[1]+90, xy[2]-30, xy[1]+90), fill=LINE, width=3)

def color(value):
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) else "#45535A"

def event_time(event):
    if event.get("all_day"):
        return "Ganzt."
    raw = str(event.get("start_datetime") or "")
    match = re.search(r"T(\d{2}:\d{2})", raw)
    return match.group(1) if match else "--:--"

def render(now, events=None, error=None, settings=None):
    settings = settings or {}
    limit = settings.get('calendarLimit', 5)
    scale = {'compact': 30, 'normal': 36, 'large': 40}.get(settings.get('calendarFontScale'), 36)
    events = events or []
    if not settings.get('showAllDay', True):
        events = [e for e in events if not e.get('all_day')]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    months = ["Januar", "Februar", "März", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]
    if settings.get('showClock', True):
        text(d, (55, 36), f"{weekdays[now.weekday()]}, {now.day}. {months[now.month-1]}", 66, True)
    d.line((55, 155, 1545, 155), fill=INK, width=5)
    if settings.get("showCalendar", True):
        panel(d, (55, 185, 970, 850), "Heute in der Familie")
    if not settings.get("showCalendar", True):
        pass
    elif error:
        text(d, (90, 310), fit(d, error, 810, 36), 36, True)
    elif not events:
        text(d, (90, 310), "Heute keine Termine", 44, True)
    else:
        ordered = sorted(events, key=lambda e: (not bool(e.get("all_day")), str(e.get("start_datetime") or "")))
        for i, event in enumerate(ordered[:limit]):
            y = 310 + i * 100
            names = event.get("assigned_users") or []
            first = names[0] if isinstance(names, list) and names else {}
            if not isinstance(first, dict): first = {}
            shade = color(first.get("avatar_color") or event.get("assigned_color") or event.get("cal_color") or event.get("local_calendar_color"))
            d.rounded_rectangle((88, y, 99, y+65), radius=4, fill=shade)
            text(d, (116, y+4), event_time(event), 35, True)
            text(d, (300, y+3), fit(d, event.get("title") or "Termin", 610, scale), scale, True)
            who = first.get("display_name") or first.get("name") or event.get("assigned_name") or ""
            if who:
                text(d, (305, y+48), fit(d, who, 580, 25), 25, False, MUTED)
        if len(ordered) > limit:
            text(d, (90, 806), f"+ {len(ordered)-limit} weitere Termine", 25, False, MUTED)
    panel(d, (1000, 185, 1545, 615), "Wetter & Kleidung")
    text(d, (1035, 330), "Noch nicht", 36, True)
    text(d, (1035, 393), "angebunden", 36)
    panel(d, (1000, 645, 1545, 850), "Stundenplan")
    text(d, (1035, 758), "Noch nicht angebunden", 30)
    panel(d, (55, 880, 1545, 1130), "Familiennotizen")
    text(d, (90, 990), "Dein Yuvomi-Familienüberblick", 39)
    text(d, (1090, 1150), "Aktualisiert: " + now.strftime("%H:%M") + " Uhr", 25, fill=MUTED)
    img = img.rotate(270, expand=True)
    output = BytesIO()
    img.save(output, "JPEG", quality=settings.get("imageQuality", 90), progressive=False, subsampling=0)
    return output.getvalue()
