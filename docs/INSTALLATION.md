# Installation · 666 RadioBotAI HYBRID v3.3.0

## 1. Umgebung vorbereiten

```bash
cp .env.example .env
```

Mindestens setzen:

```env
DISCORD_TOKEN=...
DISCORD_OWNER_ID=...
DISCORD_GUILD_ID=...
RADIO_VOICE_CHANNEL_ID=...
RADIOBOTAI_WORKER_TOKEN=...
```

## 2. Abhängigkeiten

```bash
pip install -r requirements.txt
python scripts/selftest.py
```

FFmpeg muss systemweit verfügbar sein.

## 3. Start

```bash
./start.sh
```

## 4. Discord synchronisieren

```text
!sync
```

Danach testen:

```text
/presets
/preset 1
/status
/skipstatus
/home
```

## 5. Local AutoDJ

Audiodateien ablegen in:

```text
music/666SOUNDsDESIGn/
music/Guest-Mixes/
```

Dann:

```text
/autodj
/track query:<Titel oder Interpret>
```

## 6. 24/7

- HeavenCloud: `heavencloud/STARTUP.md`
- Docker: `docker compose up -d --build`
- PM2: `pm2 start ecosystem.config.cjs && pm2 save`


## Player-Alert / Messenger

Setze `PLAYER_ALERT_WORKER_TOKEN` und nutze in Discord `/radioalert message:<Text>`. Mit `/alertstatus` wird die Worker-/Render-Verbindung geprüft. Der direkte Render-Fallback bleibt standardmäßig deaktiviert.
