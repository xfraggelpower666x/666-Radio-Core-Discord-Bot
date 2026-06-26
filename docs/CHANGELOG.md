# Changelog

## v3.3.0

- `/radioalert` für geschützte WebRadio-Player-Nachrichten ergänzt.
- `/alertstatus`, `/alertcurrent` und `/alerthistory` ergänzt.
- Cloudflare Worker bleibt Primärgateway zum Render Alert-Service.
- Optionaler direkter Render-Fallback mit eigenem Backend-Token ergänzt.
- Secrets bleiben ausschließlich in Umgebungsvariablen.

## v3.2.0

- Beide hochgeladenen Bot-Projekte final als Hybrid integriert.
- `/skipstatus` ergänzt.
- RadioBotAI Worker als primäre Skip-Bridge gesetzt.
- Admin-Worker Custom Domain und workers.dev als optionale, explizit aktivierbare Fallbacks ergänzt.
- Healthserver startet vor Discord und bleibt bei Gateway-Reconnects erreichbar.
- Kontrollierter Shutdown für AutoDJ-Tasks und Watchdog-Dateimonitor.
- HeavenCloud-, Docker- und PM2-24/7-Profile ergänzt.
- Fünf Stream-Presets und `/home` dokumentiert.

## v3.1.0

- Local AutoDJ als zweite Engine eingebunden.
- Preset-Registry, Worker-Skip, Healthserver und 24/7-Grundprofil ergänzt.
