# Yuvomi BLOOMIN8 E-Ink

Installierbares Yuvomi-Modul + lokaler Python-Docker-Relay für den BLOOMIN8 13,3-Zoll-Familienrahmen.

**[Installationsanleitung für Yuvomi und Arcane](INSTALL-MODUL.md)**

- Modul: `modules/yuvomi-bloomin8/` – direkt über die Yuvomi-GitHub-Modulinstallation installierbar.
- Relay: `service/` – Dockerfile, Kalender-API-Client, Tagesbild-Renderer, gesicherte BLOOMIN8-Pull-Endpunkte.
- Arcane Compose: `compose.arcane.yml` – lokaler Image-Build, kein GHCR erforderlich.
- Tagesansicht: heutige Yuvomi-Kalendertermine, Personenfarben, Datum, Aktualisierungszeit.
- Wetter/Kleidung, Stundenplan und Immich sind noch nicht angebunden.

Der Relay verwendet Yuvomis dokumentierte `/api/v1/calendar`-Schnittstelle mit einem lesenden Token; **kein direkter Datenbankzugriff**. Der Geräte-Token bleibt separat und wird nur serverseitig verwendet. Keine Internet-Portfreigabe erforderlich.

BLOOMIN8 Pull-Protokoll: [Schedule Pull API](https://github.com/ARPOBOT-BLOOMIN8/eink_canvas_home_assistant_component/blob/main/docs/Schedule_Pull_API.md).
Yuvomi Modul-Vertrag: [MODULES.md](https://github.com/ulsklyc/yuvomi/blob/main/MODULES.md).
