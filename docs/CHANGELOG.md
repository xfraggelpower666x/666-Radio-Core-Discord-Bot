# Changelog

## v1.3.0 - Repo-Trennung Worker/Bot

- Discord-Bot vollständig nach `discord-bot/` verschoben.
- Cloudflare Worker-Projekt unter `worker/` angelegt.
- Worker-Endpunkte ergänzt:
  - `GET /health`
  - `GET /nowplaying`
  - `GET /presets`
  - `GET /preset/1` bis `GET /preset/5`
- Root-README für Cloudflare- und Bot-Runtime-Trennung ergänzt.
- Deploy-Hinweis: Cloudflare Root Directory muss `worker` sein.
- Secrets-Regeln dokumentiert.
- Bot-Voice-Funktionen aus v1.2.0 erhalten:
  - `/play`
  - `/pause`
  - `/resume`
  - `/stop`
  - `/volume`
  - 5 Stream-Presets
  - Default-Lautstärke
  - Panel-Buttons
