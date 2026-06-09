# CHANGELOG — PHASE 2B-3D v1.1.1

## Geändert
- Discord-Shooter läuft jetzt direkt im `666radiobotai` Worker.
- WebRadio-Shooter-Logik aus dem hochgeladenen WebRadio-Repo als Vorlage übernommen:
  - `/api/discord/status`
  - `/api/discord/debug`
  - `/api/discord/manual`
  - `/api/discord/message`
  - `/api/discord/nowplaying`
- Neuer Endpunkt:
  - `/api/discord/test`
- Multi-Webhook-Ziele:
  - `DISCORD_WEBHOOK_URL` = Main / Hauptkanal
  - `DISCORD_WEBHOOK_URL2` = Secondary / Dual-Discord-Ziel
  - `DISCORD_WEBHOOK_URL3` = Channel-ID `1510363693622497400`
  - `PRIVATE_TRACK_SHOOTER` = optionaler NowPlaying-Mirror
- Dashboard-Shooter-Panel um Zielauswahl erweitert:
  - Main
  - URL2
  - URL3 / Channel 1510363693622497400
  - Alle konfigurierten Ziele
- Dashboard sendet weiterhin keine Webhook-URLs an das Frontend.

## Geschützt
- Vocard Dashboard bleibt als Basis erhalten.
- 666 RadioBotAI Bot-Core bleibt erhalten.
- Secrets bleiben ausschließlich Cloudflare Secrets / Host ENV.
- Kein Webhook im Frontend.
- Kein Ersatz des bestehenden WebRadio-Shooters.
- Keine WebRadio-Repo-Änderung.

## Offen
- Live-Test der Discord-Posts über Dashboard.
- Endgültige Benennung von URL2.
- Admin/Auth-Worker-Finalintegration.
