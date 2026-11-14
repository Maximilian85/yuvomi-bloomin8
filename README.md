# Yuvomi BLOOMIN8

Eigenständige Yuvomi-Erweiterung mit Docker-Compose-Sidecar für den BLOOMIN8 Schedule-Pull-Modus. Keine Home-Assistant-Abhängigkeit.

## Entwicklungsstand

Grundstruktur im Aufbau. Noch keine produktive Installation oder Geräteprüfung.

## Architektur

- `modules/yuvomi-bloomin8/`: Yuvomi-Oberfläche
- `service/`: HTTP-Endpunkte `/eink_pull`, `/eink_signal`, JPEG-Ausgabe
- `compose.eink.yml`: Docker-Compose-Ergänzung

Das Gerät ruft Bilder selbst über WLAN ab. Die API erwartet `X-Access-Token` und liefert `next_cron_time` in UTC. Private Konfigurationen und Zugangsdaten gehören nicht ins Repository.

Siehe [BLOOMIN8 Schedule Pull API](https://github.com/ARPOBOT-BLOOMIN8/eink_canvas_home_assistant_component/blob/main/docs/Schedule_Pull_API.md) und [Yuvomi Modul-Spezifikation](https://github.com/ulsklyc/yuvomi/blob/main/MODULES.md).
