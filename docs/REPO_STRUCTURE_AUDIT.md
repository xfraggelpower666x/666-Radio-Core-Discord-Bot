# Repo-Struktur Audit v1.3.0

## PASS

- Discord-Bot liegt unter `discord-bot/`.
- Worker liegt unter `worker/`.
- Cloudflare muss `worker` als Stammverzeichnis nutzen.
- Root enthält keine Bot-Runtime-Dateien, die versehentlich als Worker deployed werden sollen.
- Worker enthält eigenes `package.json`, `wrangler.toml` und `src/index.js`.
- Bot enthält eigenes `package.json`, `.env.example`, `src/`, `scripts/` und Startskript.
- Keine echten DJ-/Discord-/SHOUTcast-Secrets in öffentlichen Dateien.

## Offene externe Voraussetzung

Der echte SonicPanel-Button-Endpoint für AutoDJ-Skip/Jingle muss weiterhin aus dem DJ-Panel-Netzwerk-Tab oder vom Provider kommen. Ohne diesen Endpoint bleibt der SonicPanel-Skip-Adapter vorbereitet, aber nicht produktiv aktiv.
