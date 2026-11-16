# Yuvomi BLOOMIN8 – Modul und Relay installieren

## Voraussetzungen

- Yuvomi läuft bereits (offizielles Yuvomi-Image, keine Core-Änderungen).
- Der BLOOMIN8-Rahmen ist im WLAN und kann den Relay-Dienst über die Synology-IP erreichen.
- Der Synology/Arcane-Host kann die Yuvomi-URL erreichen.

## 1. Yuvomi-Modul installieren

1. In der Yuvomi-Umgebung `MODULES_ALLOW_WEB_INSTALL=true` setzen und Yuvomi neu starten. Nur nötig, wenn die Web-Installation noch deaktiviert ist.
2. Als Administrator: **Einstellungen → Module → Eigenes Modul hinzufügen → GitHub**.
3. Diese Adresse einfügen:
   `https://github.com/Maximilian85/yuvomi-bloomin8/tree/main/modules/yuvomi-bloomin8`
4. Installieren. Unter **Aktive Module** das neu installierte Modul **BLOOMIN8 E-Ink** ausdrücklich freigeben.
5. Die Modulseite zeigt die heutigen Termine direkt aus Yuvomi. Das Modul benötigt keinen zweiten Kalender.

Alternativ: Ordner `modules/yuvomi-bloomin8` in den Yuvomi-Host-Modulordner kopieren (im Container `/app/modules/yuvomi-bloomin8`). Yuvomi scannt Module zur Laufzeit.

**Sicherheit:** Web-Installation erlaubt vertrauenswürdigen Modulen JavaScript mit Benutzerrechten. Nur einschalten, wenn du die Quelle geprüft hast.

## 2. Lesenden API-Token erstellen

In Yuvomi unter **Einstellungen → Haushalt → API-Zugriff** einen Token mit **Kalender-Leseberechtigung** erstellen. Diesen nur im Arcane-Stack als `YUVOMI_API_TOKEN` eintragen, nicht in Yuvomi-Moduldateien oder GitHub.

## 3. Relay mit Arcane starten

In Arcane einen **Git/Compose-Stack** aus `https://github.com/Maximilian85/yuvomi-bloomin8.git` auf `main` anlegen. Compose-Datei `compose.arcane.yml`, Docker-Build-Kontext `./service`. Das Image wird lokal aus dem mitgelieferten Dockerfile gebaut; GHCR wird nicht benötigt.

Setze im Stack die Umgebungsvariablen:

| Variable | Beispiel | Hinweis |
|---|---|---|
| `YUVOMI_URL` | `http://192.168.0.2:3000` | **Tatsächliche** interne Yuvomi-Adresse; Port ggf. anders |
| `YUVOMI_API_TOKEN` | *(geheimer Yuvomi-Token)* | nur Kalender lesen |
| `EINK_PULL_TOKEN` | *(vorhandener Geräte-Token)* | **bestehenden** BLOOMIN8-Token beibehalten |
| `EINK_PUBLIC_URL` | `http://192.168.0.2:8088` | vom Rahmen erreichbare URL |
| `EINK_DEVICE_ID` | *(leer)* | optionaler Gerätefilter |

Der Relay-Port ist `8088`. Gesundheitsprüfung: `http://192.168.0.2:8088/health` (bei anderer Synology-IP entsprechend anpassen). Erwartet: `{"ok":true}`.

**Wichtig:** Nicht versehentlich zwei Container gleichzeitig auf Port 8088 betreiben. Den bisherigen BLOOMIN8-Testcontainer ersetzen, aber Token und Pull-URL unverändert lassen.

## 4. E-Ink-Rahmen

Wenn der Rahmen bereits erfolgreich automatisch Bilder abruft, **nichts am Rahmen ändern**. Er verwendet weiter `/eink_pull` und das signierte `dashboard_L.jpg`.

- 1600×1200 Tagesansicht, gespeichert als 1200×1600 gedrehtes Baseline-RGB-JPEG
- Aktualisierung alle 30 Minuten, Nachtpause 21:00–06:00 (Europe/Berlin)
- Echte Tages-Termine und Personen-/Kalenderfarben aus Yuvomi
- Wetter, Stundenplan, Immich **noch nicht angebunden**; werden sichtbar als Platzhalter gekennzeichnet

## Fehlerdiagnose

- Modul wird nicht angeboten: `MODULES_ALLOW_WEB_INSTALL`, Adminrolle und freigegebene Modulordner prüfen.
- Modul zeigt keine Termine: Kalender-Berechtigung des angemeldeten Benutzers prüfen.
- Relay zeigt „Yuvomi-Kalender nicht erreichbar“: `YUVOMI_URL`, Token-Leseberechtigung, Netzwerk und Container-Logs prüfen.
- Altes Bild: Arcane Image **neu bauen** und Container **neu erstellen**; nur Neustart reicht nicht.
- Geheimnisse niemals in Screenshots, Logs oder Issues veröffentlichen.
