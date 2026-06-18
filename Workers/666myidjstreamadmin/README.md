# 666myidjstreamadmin

## Status

Dieser Worker ist auf die Cloudflare-Variablen aus deinem Screenshot abgestimmt.

## Verzeichnis

```text
Workers/666myidjstreamadmin/
```

## Wrangler

```toml
name = "666myidjstreamadmin"
main = "src/index.js"
```

## Cloudflare Variablen

Bereits passend:

```text
NOWPLAYING_URL
STREAM_ADMIN_BASE_URL
STREAM_ADMIN_USER      Secret
STREAM_ADMIN_PASSWORD  Secret
STREAM_SID
```

Empfohlen zusätzlich:

```text
ADMIN_TOKEN            Secret, optional für x-admin-token Schutz
```

## Domain

```text
https://666myidjstreamadmin.666soundsdesign-broadcaster.com
```

## Worker-Dev

```text
https://666myidjstreamadmin.digital-underground-connected.workers.dev
```

## Deploy

```bash
cd Workers/666myidjstreamadmin
npx wrangler deploy
```

## Endpoints

```text
GET  /health
GET  /status
GET  /config/public
GET  /nowplaying
POST /admin/autodj/skip
POST /admin/autodj/playlist-switch
GET  /admin/stream/status
```
