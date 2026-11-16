"""Readable 1600x1200 daily family overview for the BLOOMIN8 e-ink display."""
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1200
INK = "#18262C"
MUTED = "#45535A"
BG = "#FAFAF7"
LINE = "#BAC3C3"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def font(size, bold=False):
    try:
        return ImageFont.truetype(BOLD if bold else FONT, size)
    except OSError:
        # The Docker image installs fonts-dejavu-core. Fail explicitly if missing.
        raise RuntimeError("DejaVu fonts missing; rebuild Docker image")

def text(draw, xy, value, size, bold=False, fill=INK):
    draw.text(xy, value, font=font(size, bold), fill=fill)

def panel(draw, xy, title):
    draw.rounded_rectangle(xy, radius=20, fill="#FFFFFF", outline=LINE, width=3)
    text(draw, (xy[0]+34, xy[1]+24), title, 43, True)
    draw.line((xy[0]+34, xy[1]+91, xy[2]-34, xy[1]+91), fill=LINE, width=3)

def render(now):
    local = now
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    months = ["Januar", "Februar", "März", "April", "Mai", "Juni",
              "Juli", "August", "September", "Oktober", "November", "Dezember"]
    text(d, (55, 36), f"{weekdays[local.weekday()]}, {local.day}. {months[local.month-1]}", 66, True)
    d.line((55, 155, 1545, 155), fill=INK, width=5)
    panel(d, (55, 185, 970, 850), "Heute in der Familie")
    text(d, (90, 320), "Noch keine Kalender verbunden", 47, True)
    text(d, (90, 415), "Hier erscheinen die heutigen Termine", 37)
    text(d, (90, 475), "mit Uhrzeit und Familienfarbe.", 37)
    panel(d, (1000, 185, 1545, 615), "Wetter & Kleidung")
    text(d, (1035, 330), "Wetter noch nicht", 36, True)
    text(d, (1035, 392), "eingerichtet", 36)
    panel(d, (1000, 645, 1545, 850), "Stundenplan")
    text(d, (1035, 758), "Noch nicht verbunden", 31)
    panel(d, (55, 880, 1545, 1130), "Familiennotizen")
    text(d, (90, 990), "Das erste Yuvomi-Tagesdashboard ist bereit.", 39)
    text(d, (1070, 1150), "Aktualisiert: " + local.strftime("%H:%M") + " Uhr", 26, False, MUTED)
    # BLOOMIN8 expects a portrait JPEG containing the rotated landscape layout.
    img = img.rotate(270, expand=True)
    out = BytesIO()
    img.save(out, "JPEG", quality=90, progressive=False, subsampling=0)
    return out.getvalue()
