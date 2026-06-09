# 666 RadioBotAI — Render Backend Integration v1.1.3

Status: UPLOAD-READY / CODE-AUDIT PASS  
Zeit: 2026-06-09T19:37:38+00:00

## Korrektur

Der WebRadio-Code enthaelt bereits ein Renderer/Render Backend unter:

```text
renderer-resources/666SOUNDsDESIGn-Alert-Service-Renderer/
```

Dieses Backend ist kein Discord-Voice-Bot-Host, sondern ein Backend-primary Relay fuer Player/Broadcast Alerts. Die Logik wurde in RadioBotAI v1.1.3 uebernommen.

## Uebernommene Backend-Routen

```text
GET  /health
GET  /api/player-alert/status
POST /api/player-alert/send
GET  /api/player-alert/current
GET  /api/player-alert/history
```

## Worker-Bridge v1.1.3

Neue Worker-Routen:

```text
GET  /render/status
GET  /api/player-alert/status
POST /api/player-alert/send
GET  /api/player-alert/current
GET  /api/player-alert/history
```

Fallback-Reihenfolge wie im WebRadio-Code:

```text
Render Backend -> PLAYER_ALERT_KV -> Cloudflare Cache
```

## ENV / Variables

```text
PLAYER_ALERT_BACKEND_URL=https://<render-service>.onrender.com
PLAYER_ALERT_KV=<optional Cloudflare KV Binding>
PLAYER_ALERT_TTL_SECONDS=900
PLAYER_ALERT_MAX_HISTORY=30
SYSTEM_PW_WORKER_URL=https://666-system-pw.666soundsdesign-broadcaster.com
ADMIN_AUTH_VERIFY_URL=https://666-system-auth.666soundsdesign-broadcaster.com/verify
```

## Sicherheit

- Keine Secret-Werte im Repo.
- Backend-URL darf als Worker-Variable gesetzt werden.
- Player Alert Send ist im RadioBotAI Worker ueber Admin/Auth geschuetzt.
- Render Backend selbst bleibt Secret-frei im Repo; echte Werte nur in Render ENV.

## Wichtig

Der Discord Voice Bot bleibt ein separater Runtime-Prozess. Diese Integration schliesst den fehlenden Renderer/Render Backend Relay, nicht automatisch den Voice-Bot-Host.
