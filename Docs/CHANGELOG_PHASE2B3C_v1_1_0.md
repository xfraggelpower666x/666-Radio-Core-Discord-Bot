# CHANGELOG — PHASE 2B-3C VOCARD SOVEREIGN DASHBOARD MERGE v1.1.0

Erstellt: 2026-06-09 04:17 UTC

## Hinzugefügt

- Vocard-Dashboard als Hauptbasis unter `Dashboard/Vocard-Dashboard-main/` erhalten.
- Vocard-Installer als Installer-Basis unter `Installer/Vocard-Installer-main/` erhalten.
- 666-RadioBotAI Core unter `Discord-Bot/666-RadioBotAI/` integriert.
- Cloudflare Worker unter `Arbeiter/src/index.js` programmiert.
- Root-`wrangler.toml` mit `main = "Arbeiter/src/index.js"` ergänzt.
- Cyberstream Dashboard Route `/dashboard` programmiert.
- Stream Preview, NowPlaying, Status, Presets, Discord-Shooter Panel und Admin/Auth-Test im Dashboard ergänzt.
- `.env.example` ohne echte Secrets ergänzt.

## Repariert / Gepatcht

- Volume-Standard im 666-RadioBotAI Core von 0–500 auf 0–200 gesetzt.
- Default Volume auf 100 gesetzt.
- Safe Max 150 / Boost Max 200 dokumentiert.

## Geschützt

- Originale Vocard-Dashboard-Dateien nicht überschrieben.
- Originale Vocard-Installer-Dateien nicht überschrieben.
- Keine Webhook-URLs ins Frontend geschrieben.
- Keine echten Secrets in Repo-Dateien geschrieben.
- Discord Voice Bot nicht als Cloudflare Worker behandelt.

## Offen

- Cloudflare Deploy live testen.
- Dashboard-Shooter gegen echte WebRadio-Shooter-Secrets/Auth testen.
- Auth-/Passwort-Worker-Routen final prüfen.
- Vocard-Dashboard-Frontend bei Bedarf tiefer in die RadioBotAI-Addon-UI einhängen.
