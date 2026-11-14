# Installation und BLOOMIN8-Hardwaretest (Linux Mint)

**Status:** Pull-Protokoll-Test, noch kein produktives Yuvomi-Dashboard. Dieser Test zeigt ein eigenes Bild mit Datum/Uhrzeit. Kalender, Immich, Wetter und UI-Einstellungen sind noch nicht angebunden.

## Voraussetzungen

- Linux Mint mit Docker Engine und Docker-Compose-Plugin (`docker compose version`)
- BLOOMIN8 13,3" und Linux-Mint-Host im selben erreichbaren WLAN/LAN
- IP-Adresse des Linux-Mint-Hosts (Beispiel `192.168.1.50`)
- Gerät muss wach und im WLAN sein, um Pull-Einstellungen zu ändern
- Port **8088/TCP** vom Rahmen zum Linux-Mint-Rechner erreichbar
- **Keine Portfreigabe am Router** und keine öffentliche Exposition

## 1. Code holen

Der Hardwaretest liegt zunächst im Entwicklungsbranch. Auf Linux Mint im Terminal:

```bash
git clone --branch feature/bloomin8-pull-mvp https://github.com/Maximilian85/yuvomi-bloomin8.git
cd yuvomi-bloomin8
cp .env.example .env
```

Bei einem privaten Repository benötigst du eine passende GitHub-Anmeldung (z.B. Git Credential Manager, GitHub CLI `gh auth login` oder SSH). Keine GitHub-Tokens in diesen Chat kopieren.

## 2. Konfiguration

LAN-IP des Hosts herausfinden:

```bash
hostname -I
```

Ein langes zufälliges Token erzeugen:

```bash
openssl rand -hex 32
```

Datei `.env` mit Texteditor bearbeiten:

```bash
xed .env
```

- `EINK_PULL_TOKEN`: den erzeugten Wert einsetzen (mindestens 24 Zeichen)
- `EINK_PUBLIC_URL`: `http://DEINE-LINUX-MINT-IP:8088` — **nicht** localhost oder Docker-Containername
- `EINK_DEVICE_ID`: für den ersten Test **leer lassen**; der geheime Token schützt den Abruf. Später anhand der Serverlogs auf die Geräte-ID einschränken.
- `EINK_INTERVAL_MINUTES=30`, `EINK_NIGHT_START=21`, `EINK_NIGHT_END=6`

`.env` niemals in Git committen.

## 3. Container starten

```bash
docker compose -f compose.eink.yml up -d --build
docker compose -f compose.eink.yml ps
curl -i http://127.0.0.1:8088/health
```

Erwartet: `HTTP/1.1 200 OK` und `{"ok": true}`.

Falls Linux Mint eine Firewall aktiviert hat: ausschließlich im vertrauenswürdigen LAN TCP 8088 freigeben. Router-Portweiterleitung ist **nicht** erforderlich.

## 4. Pull lokal simulieren

```bash
set -a; source .env; set +a
curl -sS -H "X-Access-Token: $EINK_PULL_TOKEN" \
  "http://127.0.0.1:8088/eink_pull?device_id=test-device&pull_id=manual-001&battery=90"
```

Tagsüber erwartet: JSON mit `"status":200`, `"type":"SHOW"`, `data.image_url` und `data.next_cron_time`. Zwischen 21:00 und 06:00 Ortszeit: `"status":204` und nächste Zeit ab 06:00.

**Wichtig:** Der Bild-Link ist nur 15 Minuten gültig. Er enthält eine zeitlich begrenzte Signatur, nicht den Haupttoken. Der Rahmen muss den Link sofort laden.

## 5. BLOOMIN8 aktivieren

Geräte-IP ermitteln (Router oder BLOOMIN8-App). Das Gerät muss eingeschaltet/erreichbar sein.

Auf Linux Mint zunächst die **Geräte-Einstellungen ansehen**:

```bash
curl -sS http://DEINE-RAHMEN-IP/upstream/pull_settings
```

Um den ersten Test unmittelbar auszulösen, eine UTC-Zeit ca. 2 Minuten in der Zukunft erzeugen:

```bash
date -u -d '+2 minutes' +'%Y-%m-%dT%H:%M:%SZ'
```

Die angezeigte Zeit und Werte in den folgenden Befehl eintragen. **Achtung:** Dadurch werden die Pull-Einstellungen des Rahmens verändert.

```bash
curl -i -X PUT "http://DEINE-RAHMEN-IP/upstream/pull_settings" \
  -H "Content-Type: application/json" \
  --data '{"upstream_on":true,"upstream_url":"http://DEINE-LINUX-MINT-IP:8088","token":"DEIN_LANGES_TOKEN","cron_time":"2026-11-14T12:00:00Z"}'
```

**Die Beispielzeit unbedingt ersetzen!** `cron_time` muss eine **zukünftige UTC-Zeit** mit `Z` sein. Token muss exakt mit `.env` übereinstimmen.

Anschließend:

```bash
docker compose -f compose.eink.yml logs -f --tail=100
```

Erwartet: `GET /eink_pull`, dann `GET /images/dashboard_L.jpg`, optional `GET /eink_signal`. Auf dem Display erscheint ein Querformat-Testbild mit „Yuvomi BLOOMIN8“. Tagsüber erfolgt der nächste Abruf nach 30 Minuten; während der Nachtpause wird bis frühestens 06:00 gewartet.

Nach dem ersten Pull steht die Geräte-ID in der Logzeile `pull from device_id=...`. Optional in `.env` bei `EINK_DEVICE_ID` eintragen und Container neu starten.

## 6. Fehlersuche

- **Kein Pull:** Gerät schläft, WLAN nicht verbunden, falsche IP oder Startzeit liegt in der Vergangenheit. Geräteeinstellungen per GET prüfen.
- **401:** Token in Rahmen und `.env` stimmt nicht überein.
- **Bild fehlt:** LAN-IP oder Port 8088 vom Rahmen nicht erreichbar; Bildlink nach 15 Minuten abgelaufen; Host-Firewall.
- **204 statt Bild:** geplante Nachtpause von 21:00 bis 06:00.
- **Bild gedreht:** Foto des Displays und Firmwareversion notieren; die Bilddatei ist absichtlich 1200×1600 Pixel mit `_L.jpg`-Suffix.
- **Containerfehler:** `docker compose -f compose.eink.yml logs --tail=100`.
- **Prüfen, ob Bild ohne Redirect/Chunking ausgeliefert wird:** signierte `image_url` aus der JSON-Antwort unmittelbar mit `curl -I 'URL'` testen. `Content-Length` muss numerisch sein.

## 7. Test beenden

Pull am Rahmen deaktivieren:

```bash
curl -i -X PUT "http://DEINE-RAHMEN-IP/upstream/pull_settings" \
  -H "Content-Type: application/json" --data '{"upstream_on":false}'
```

Danach Container stoppen:

```bash
docker compose -f compose.eink.yml down
```

## Was für den nächsten Entwicklungsschritt hilfreich ist

Teile bei Problemen **bereinigte** Logs, die Firmwareversion, die sichtbare Bildorientierung und ob der Rahmen den nächsten Pull ausführt. Bitte keine Tokens, signierten Bild-URLs, privaten IPs (falls nicht gewünscht) oder Zugangsdaten veröffentlichen.
