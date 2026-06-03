# Secrets-Regeln

## Niemals öffentlich speichern

```text
DISCORD_TOKEN
DISCORD_CLIENT_ID, falls nicht öffentlich gewollt
DISCORD_GUILD_ID, falls nicht öffentlich gewollt
SONICPANEL_DJ_USER
SONICPANEL_DJ_PASS
SHOUTCAST_ADMIN_PASS
Webhook-URLs
Bearer-Tokens
Cookies
Session-IDs
```

## Discord-Bot

Echte Werte nur in:

```text
discord-bot/.env
```

## Cloudflare Worker

Echte geheime Werte nur als Cloudflare Secret oder geschützte Environment Variable setzen.

## Repo-Regel

`.env`, `.dev.vars`, Logs und lokale Runtime-Dateien sind per `.gitignore` ausgeschlossen.
