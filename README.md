# 666 RadioBotAI — Vocard Sovereign Root v1.1.3

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


## v1.1.3 — Direct Discord Shooter Update

Der Discord-Shooter läuft jetzt direkt im Worker `666radiobotai` und nutzt Cloudflare Secrets:

- `DISCORD_WEBHOOK_URL` = Main / Hauptkanal
- `DISCORD_WEBHOOK_URL2` = Secondary / Dual-Discord-Ziel aus WebRadio-Logik
- `DISCORD_WEBHOOK_URL3` = Channel-ID `1510363693622497400`
- `PRIVATE_TRACK_SHOOTER` = optionaler NowPlaying-Mirror-Kompatibilitätsname

Dashboard-Endpunkte:

- `GET /api/discord/status`
- `GET /api/discord/debug`
- `POST /api/discord/message`
- `POST /api/discord/manual`
- `POST /api/discord/nowplaying`
- `POST /api/discord/test`

Webhook-URLs werden niemals an das Frontend ausgegeben.

## v1.1.3 Admin/Auth Deep Integration

Dieser Stand ergänzt einen geschützten Admin-Bereich für Dashboard-Steuerfunktionen.

Neue Routen:

- `/auth/status`
- `/auth/verify`
- `/admin/status`
- `/admin/protected-test`

Geschützte Aktionen werden serverseitig geprüft. Das Frontend enthält keine Webhook-URLs, Tokens oder Passwörter.
