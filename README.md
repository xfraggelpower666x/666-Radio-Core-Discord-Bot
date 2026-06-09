# 666 RadioBotAI — Vocard Sovereign Root v1.1.0

Dieses Paket ist die Vocard-basierte RadioBotAI-Root-Struktur für die Repo `xfraggelpower666x/666RadioBotAI` auf Branch `666RadioBotAI`.

## Struktur

- `Arbeiter/` — Cloudflare Worker für API, Dashboard, Status, Stream, Shooter-Bridge.
- `Dashboard/Vocard-Dashboard-main/` — originale Vocard-Dashboard-Basis, erhalten und nicht ersetzt.
- `Dashboard/radiobotai-addon/` — RadioBotAI Dashboard-Erweiterung für Stream, Status, Shooter und Admin/Auth.
- `Discord-Bot/666-RadioBotAI/` — Bot-Core auf Basis von 666-RadioBotAI v1.0.0, mit Volume-Standard 0–200 gepatcht.
- `Installer/Vocard-Installer-main/` — Vocard Installer-Basis.
- `Docs/` — Audit, Changelog, Upload-Hinweise.

## Cloudflare Deploy

Cloudflare kann weiter aus dem Repo-Root deployen:

```bash
npx wrangler deploy
```

`wrangler.toml` zeigt auf:

```toml
main = "Arbeiter/src/index.js"
```

## Wichtige Endpunkte

- `/health`
- `/status`
- `/nowplaying`
- `/stream`
- `/dashboard`
- `/config/public`
- `/api/discord/status`
- `/api/discord/manual`
- `/api/discord/message`
- `/api/discord/nowplaying`
- `/auth/verify`
- `/preset/1` bis `/preset/5`

## Sicherheit

Keine echten Tokens, Webhooks, Passwörter oder SonicPanel-Zugangsdaten in dieses Repo schreiben. Nutze Cloudflare Secrets, Host-ENV oder lokale `.env` außerhalb von Git.

## Buildstand

Erstellt: 2026-06-09 04:17 UTC
Status: Upload-ready / kein Produktions-Freeze ohne Cloudflare-Test.
