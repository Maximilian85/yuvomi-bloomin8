> **Hinweis (GHCR-Vorbereitung):** Das Projekt enthält jetzt einen GitHub-Actions-Workflow `.github/workflows/publish.yml`, der nach Übernahme in `main` das Image `ghcr.io/maximilian85/yuvomi-bloomin8:latest` bauen und veröffentlichen soll. **Noch nicht veröffentlicht oder als erfolgreich getestet.** Das GHCR-Paket muss nach dem ersten Build in GitHub unter Package settings auf **Public** gestellt werden. Danach kann Arcane `compose.arcane.yml` ohne SSH und ohne lokalen Docker-Build verwenden. Bis dahin gelten die folgenden manuellen Build-Schritte als Ausweichweg. Die GitHub-Actions-Testchecks sollten vor dem Merge erfolgreich sein.

# Hardwaretest auf Synology NAS mit Arcane

**Ziel:** BLOOMIN8 13,3" testweise per Schedule Pull von einem Docker-Container auf der Synology versorgen. Yuvomi bleibt unverändert. Der Dienst zeigt zunächst nur ein Testbild, **keine** Kalender-/Immich-/Wetterdaten.

## Voraussetzungen

- Synology NAS als Docker-Host, Arcane verwaltet Docker-Compose-Stacks
- Synology und BLOOMIN8 im gleichen erreichbaren LAN/WLAN
- IP-Adresse der Synology und des BLOOMIN8-Rahmens
- Für die **erste Image-Erstellung** Zugriff auf Docker CLI auf der Synology (SSH) **oder** eine Arcane-Funktion, die ein Repository mit Dockerfile bauen kann
- TCP-Port 8088 von BLOOMIN8 zur Synology erreichbar; **keine Router-Portfreigabe**
- Private GitHub-Repository-Berechtigung

## 1. Container-Image bereitstellen

Es ist noch **kein veröffentlichtes Registry-Image** vorhanden. Deshalb muss das Image einmal aus dem Repository gebaut werden. Die folgende Variante funktioniert unabhängig davon, ob Arcane selbst einen Build-Kontext aus Git unterstützt.

Auf der Synology per SSH (nur innerhalb des LANs, SSH nach Bedarf in DSM aktivieren):

```bash
git clone --branch feature/bloomin8-pull-mvp https://github.com/Maximilian85/yuvomi-bloomin8.git
cd yuvomi-bloomin8
sudo docker build -t yuvomi-bloomin8:hardware-test ./service
```

Das Repository ist privat; Git verlangt eine gültige Anmeldung. **Keine Tokens in Arcane-Compose-Dateien, Git oder diesen Chat kopieren.**

Falls `git` auf der Synology nicht verfügbar ist, das Repository als ZIP auf einem anderen Gerät herunterladen und den Ordner `service/` auf die Synology kopieren. Dann dort `docker build -t yuvomi-bloomin8:hardware-test /PFAD/ZUM/service` ausführen.

**Alternative:** Wenn deine Arcane-Version einen Git-Checkout mit Build-Kontext unterstützt, kannst du die Datei `compose.eink.yml` direkt aus dem Repository nutzen. Ob diese Funktion bei dir verfügbar ist, müssen wir in Arcane prüfen.

## 2. Arcane-Compose-Stack erstellen

In Arcane einen **neuen, separaten Compose-Stack** erstellen (nicht den bestehenden Yuvomi-Stack überschreiben) und den Inhalt von `compose.arcane.yml` einfügen. **Diese Datei erwartet inzwischen das veröffentlichte GHCR-Image.** Vor der ersten Veröffentlichung stattdessen das manuell gebaute Image `yuvomi-bloomin8:hardware-test` im Compose-Eintrag `image:` verwenden.

In Arcane die folgenden Umgebungsvariablen für den Stack konfigurieren (falls Arcane Variableninterpolation anbietet), andernfalls lokal in einer nicht versionierten `.env` hinterlegen:

- `EINK_PULL_TOKEN`: zufälliger Wert mit mindestens 24 Zeichen, z. B. durch `openssl rand -hex 32`
- `EINK_PUBLIC_URL`: `http://SYNOLOGY-LAN-IP:8088`
- `EINK_DEVICE_ID`: beim ersten Test leer lassen; später aus Logs übernehmen
- `TZ=Europe/Berlin`

Andere Werte: `EINK_INTERVAL_MINUTES=30`, `EINK_NIGHT_START=21`, `EINK_NIGHT_END=6`.

**Achtung:** Der Token darf nicht im Git-Repository landen. Arcane zeigt eventuell die Compose-Konfiguration für Administratoren an.

Den Stack deployen. Die Synology-Firewall muss TCP 8088 aus dem lokalen Netz zulassen.

## 3. Synology-Dienst prüfen

Vom Rechner oder Handy im gleichen LAN:

```text
http://SYNOLOGY-LAN-IP:8088/health
```

Erwartet: `{"ok": true}`.

Alternativ über Arcane die Container-Logs öffnen. Der Dienst muss laufen und auf Port 8088 lauschen.

## 4. BLOOMIN8 konfigurieren

Rahmen aufwecken, WLAN prüfen und seine IP ermitteln. **Die Konfiguration wird am Gerät vorgenommen**, nicht in Arcane.

Zuerst die aktuelle Konfiguration abrufen:

```bash
curl http://RAHMEN-IP/upstream/pull_settings
```

Für den Test eine UTC-Zeit etwa 2 Minuten in der Zukunft erzeugen:

```bash
date -u -d '+2 minutes' +'%Y-%m-%dT%H:%M:%SZ'
```

Dann den Rahmen konfigurieren:

```bash
curl -X PUT "http://RAHMEN-IP/upstream/pull_settings" \
  -H "Content-Type: application/json" \
  --data '{"upstream_on":true,"upstream_url":"http://SYNOLOGY-LAN-IP:8088","token":"DEIN_LANGES_TOKEN","cron_time":"ZUKUENFTIGE-UTC-ZEIT"}'
```

**Beispielwerte ersetzen.** Die UTC-Zeit muss ISO 8601 mit `Z` sein, etwa `2026-11-14T15:30:00Z`. Der Token muss exakt dem Wert aus Arcane entsprechen.

## 5. Ergebnis kontrollieren

In Arcane die Logs des BLOOMIN8-Containers öffnen.

Erwartete Anfragen:

1. `GET /eink_pull` – Rahmen fragt nach dem Bild
2. `GET /images/dashboard_L.jpg` – Rahmen lädt das JPEG
3. Optional `GET /eink_signal` – Rahmen bestätigt das Ergebnis

Auf dem BLOOMIN8 erscheint ein Querformat-Testbild. Das Bild wird als Baseline-RGB-JPEG mit 1200×1600 Pixeln und `_L.jpg`-Suffix übertragen.

Der nächste Pull wird auf 30 Minuten später geplant. Von 21:00 bis 06:00 Uhr (Europe/Berlin) wird kein neues Bild ausgeliefert.

**Wichtig:** Die Bild-URL ist nur 15 Minuten gültig. Der Rahmen muss sie sofort abrufen.

## 6. Fehlerbehebung

- **Container startet nicht:** Arcane-Logs prüfen; existiert das lokal gebaute Image `yuvomi-bloomin8:hardware-test` auf demselben Docker-Host?
- **Health-Endpunkt nicht erreichbar:** Synology-LAN-IP, Port 8088 und DSM-Firewall prüfen.
- **401 beim Pull:** Token stimmt nicht überein.
- **204 im JSON:** Nachtpause aktiv.
- **Kein Bild trotz Pull:** Erreichbarkeit der Bild-URL und `Content-Length` prüfen; signierte URL nicht öffentlich teilen.
- **Falsche Bildausrichtung:** Firmwareversion und Foto des Testbilds notieren.
- **Kein Pull:** Rahmen möglicherweise im Standby, WLAN getrennt oder `cron_time` ungültig.

## 7. Test beenden

```bash
curl -X PUT "http://RAHMEN-IP/upstream/pull_settings" \
  -H "Content-Type: application/json" \
  --data '{"upstream_on":false}'
```

Anschließend in Arcane den BLOOMIN8-Stack stoppen.

## Testumfang und Einschränkungen

Die Integrationstests liegen unter `tests/`, der GitHub-Actions-Workflow unter `.github/workflows/test.yml`. Ein erfolgreicher CI-Lauf und ein Test auf echter BLOOMIN8-Hardware sind noch **nicht bestätigt**. Das Yuvomi-Modul ist noch nicht als installierbar validiert. Bitte den Entwicklungs-Pull-Request noch nicht mergen und Port 8088 nicht ins Internet öffnen.
