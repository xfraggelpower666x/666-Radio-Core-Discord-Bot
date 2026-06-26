# HeavenCloud 24/7 Startprofil

## Empfohlener Startup-Befehl

```bash
./start.sh
```

Alternativ:

```bash
python -u main.py
```

## Pflichtvariablen

```env
DISCORD_TOKEN=...
DISCORD_OWNER_ID=...
DISCORD_GUILD_ID=...
RADIO_VOICE_CHANNEL_ID=...
RADIOBOTAI_WORKER_TOKEN=...
PORT=8080
HEALTH_PORT=8080
```

## Port / Healthcheck

- Container-Port: `8080`
- Liveness: `/healthz`
- Readiness: `/readyz`
- Root: `/`

Der Healthserver startet vor der Discord-Gateway-Verbindung. Ein Discord-Ausfall beendet deshalb nicht den Prozess-Healthcheck.

## 24/7-Schutz

- Prozess-Neustart durch HeavenCloud/Pterodactyl aktivieren.
- `AUTO_RECONNECT=true`
- `AUTO_JOIN_ON_READY=true`
- `DISCONNECT_WHEN_ALONE=false`
- Genügend RAM für Python, FFmpeg und die lokale Musikbibliothek reservieren.
- Persistente Volumes/Ordner für `db/`, `runtime/`, `music/` und `botconfig/` erhalten.

## Vor dem ersten Start

```bash
cp .env.example .env
python scripts/selftest.py
```

Für `/radioalert` wird standardmäßig `RADIOBOTAI_WORKER_TOKEN` mitverwendet. `PLAYER_ALERT_WORKER_TOKEN` ist nur nötig, wenn dafür ein getrenntes Secret eingesetzt werden soll.

Secrets niemals in ZIP, GitHub oder öffentliche Logs schreiben.
