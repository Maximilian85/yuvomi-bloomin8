# Yuvomi BLOOMIN8

LAN-basierter Pull-Dienst für den BLOOMIN8 13,3"-Farb-E-Ink-Rahmen. Ohne Home Assistant.

## Aktueller Stand: Hardware-Smoke-Test

- Docker-Compose-Sidecar mit `/eink_pull`, `/eink_signal`, `/health`
- Querformat-Testbild als 1200×1600 Baseline-RGB-JPEG (`_L.jpg`)
- Geräte-Token, kurzlebige signierte Bildlinks, optionaler Geräte-ID-Filter
- 30-Minuten-Intervall, Nachtpause 21:00–06:00 Europe/Berlin
- HTTP- und Bildtests in GitHub Actions

**[Installations- und Hardwaretest-Anleitung](INSTALLATION.md)**

Noch nicht integriert: echte Yuvomi-Kalenderdaten, Personenfarben, Wetter, Kleidung, Immich und konfigurierbare Yuvomi-Oberfläche. Das Modul unter `modules/` ist nur ein Platzhalter und nicht als Yuvomi-kompatibel verifiziert.

Entwicklung erfolgt im Branch `feature/bloomin8-pull-mvp`. Keine Portfreigabe ins Internet.

Protokoll: [BLOOMIN8 Schedule Pull API](https://github.com/ARPOBOT-BLOOMIN8/eink_canvas_home_assistant_component/blob/main/docs/Schedule_Pull_API.md).
