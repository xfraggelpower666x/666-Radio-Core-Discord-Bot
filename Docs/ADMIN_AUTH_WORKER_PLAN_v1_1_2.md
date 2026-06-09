# 666 RadioBotAI — Admin/Auth Worker Plan v1.1.2

## Ziel

Das Dashboard bleibt öffentlich lesbar, aber Steuerfunktionen werden geschützt.

## Öffentliche Bereiche

- `/dashboard`
- `/status`
- `/nowplaying`
- `/stream`
- `/auth/status`
- `GET /preset/1..5` read-only

## Geschützte Bereiche

- `POST /api/discord/message`
- `POST /api/discord/manual`
- `POST /api/discord/nowplaying`
- `POST /api/discord/test`
- `POST /preset/1..5`
- `/admin/status`
- `/admin/protected-test`

## Auth-Reihenfolge

1. `x-admin-token` gegen `DISCORD_ADMIN_TOKEN` oder `ADMIN_TOKEN`
2. `x-discord-gate-code` gegen `DISCORD_GATE_CODE`
3. `authorization` gegen externen Auth-Worker via `ADMIN_AUTH_VERIFY_URL` oder `AUTH_VERIFY_URL`
4. Passwort-Worker via `ADMIN_PASSWORD_VERIFY_URL`, `ADMIN_PW_VERIFY_URL`, `PASSWORD_VERIFY_URL` oder `PW_VERIFY_URL`
5. Legacy Gate SHA256 Kompatibilität für alte Shooter-Logik

## Sicherheit

- Frontend speichert nichts dauerhaft.
- Eingabe bleibt nur im Browserfeld.
- Worker gibt nur Boolean-/Statuswerte zurück.
- Keine Secretwerte in Antworten.
