# Cloudflare Worker Bridge

## Verwendete Rollen

```text
Discord /skip
  -> https://666radiobotai.666soundsdesign-broadcaster.com/radio/autodj/skip
  -> RADIO_ADMIN_WORKER_URL/admin/autodj/skip
  -> SHOUTcast / AutoDJ Admin-Aktion
```

## Bestätigte öffentliche Worker-Basis

- RadioBotAI Worker: `https://666radiobotai.666soundsdesign-broadcaster.com`
- Admin-Worker Custom Domain: `https://666myidjstreamadmin.666soundsdesign-broadcaster.com`
- Admin-Worker workers.dev Fallback: `https://666myidjstreamadmin.digital-underground-connected.workers.dev`

Die Root-Antworten der beiden Admin-Domains zeigen aktuell dieselbe öffentliche Service-Signatur wie der RadioBotAI Worker. Deshalb ist `RADIO_ADMIN_DIRECT_FALLBACK=false` der sichere Standard. Erst nach einem erfolgreichen geschützten Test von `POST /admin/autodj/skip` darf der direkte Fallback aktiviert werden.

## Bot-Variablen

```env
RADIOBOTAI_WORKER_URL=https://666radiobotai.666soundsdesign-broadcaster.com
RADIOBOTAI_WORKER_SKIP_PATH=/radio/autodj/skip
RADIOBOTAI_WORKER_STATUS_PATH=/radio/autodj/status
RADIOBOTAI_WORKER_TOKEN=...

RADIO_ADMIN_WORKER_URL=https://666myidjstreamadmin.666soundsdesign-broadcaster.com
RADIO_ADMIN_WORKER_FALLBACK_URL=https://666myidjstreamadmin.digital-underground-connected.workers.dev
RADIO_ADMIN_WORKER_SKIP_PATH=/admin/autodj/skip
RADIO_ADMIN_WORKER_TOKEN=...
RADIO_ADMIN_DIRECT_FALLBACK=false
```

## Testreihenfolge

1. `/skipstatus` im Discord ausführen.
2. Geschützten Worker-Test über `/admin/protected-test` prüfen.
3. `/skip` während eines echten AutoDJ-Titels ausführen.
4. Erst bei nachgewiesenem Admin-Pfad den direkten Fallback aktivieren.
