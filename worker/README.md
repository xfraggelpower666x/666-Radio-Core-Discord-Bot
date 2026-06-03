# 666RadioCoreDJ Worker

Cloudflare Worker API-Layer für Status und Stream-Preset-Informationen.

## Deploy in Cloudflare

```text
Root directory: worker
Build command: leer
Deploy command: npx wrangler deploy
```

## Lokale Prüfung

```bash
npm run check
npx wrangler dev
```

## Endpunkte

```text
GET /health
GET /nowplaying
GET /presets
GET /preset/1
GET /preset/2
GET /preset/3
GET /preset/4
GET /preset/5
```

## Secrets

Keine Admin-Passwörter in `wrangler.toml` schreiben. Für echte geheime Werte Cloudflare Secrets verwenden.
