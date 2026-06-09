# CHANGELOG — PHASE 2B-4B / v1.1.3

Zeit: 2026-06-09T19:37:38+00:00

## Hinzugefuegt

- `Render/666RadioBotAI-PlayerAlert-Render-Backend/` aus WebRadio Renderer-Ressource uebernommen.
- `render.yaml` fuer RadioBotAI Player Alert Backend angepasst.
- `.env.render.example` ohne echte Secrets hinzugefuegt.
- Worker-Bridge fuer `/api/player-alert/*` eingebaut.
- `/render/status` eingebaut.
- Dashboard-Tab `Broadcast Relay` eingebaut.
- Fallback-Reihenfolge `Render Backend -> KV -> Cache` uebernommen.

## Korrigiert

- v1.1.2 hatte Admin/Auth, aber kein Renderer/Render Backend Relay.
- v1.1.3 integriert die vorhandene WebRadio-Logik gezielt in RadioBotAI.

## Geschuetzt

- Keine Secrets in Dateien.
- Webhook-Secrets bleiben Cloudflare Secrets.
- Admin/Auth bleibt fuer Send-Aktionen aktiv.
