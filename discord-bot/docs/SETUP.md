# 666RadioCoreDJ Setup

## 1. Dateien vorbereiten

```bash
cp .env.example .env
npm install
```

Unter Windows kannst du auch nutzen:

```powershell
.\start-666RadioCoreDJ.ps1 -Install
```

## 2. Discord-Werte setzen

In `.env`:

```env
DISCORD_TOKEN=...
DISCORD_CLIENT_ID=...
DISCORD_GUILD_ID=...
RADIO_TEXT_CHANNEL_ID=...
RADIO_LOG_CHANNEL_ID=...
ALLOWED_ROLE_IDS=...
```

## 3. Stream-Presets setzen

Bis zu fünf Streams:

```env
VOICE_DEFAULT_PRESET=1
VOICE_DEFAULT_VOLUME_PERCENT=80
VOICE_MAX_VOLUME_PERCENT=200

STREAM_PRESET_1_NAME=Main Radio
STREAM_PRESET_1_URL=http://DEIN_STREAM_HOST:PORT/stream
STREAM_PRESET_1_VOLUME_PERCENT=80

STREAM_PRESET_2_NAME=Backup Stream
STREAM_PRESET_2_URL=
STREAM_PRESET_2_VOLUME_PERCENT=80
```

Wenn du nur einen Stream nutzt, reicht Preset 1 oder `RADIO_STREAM_URL`.

ICY-Metadaten und Health-Checks laufen automatisch fuer http(s)-SHOUTcast/Icecast-Streams:

```env
STREAM_HEALTH_INTERVAL_SECONDS=30
STREAM_HEALTH_TIMEOUT_SECONDS=10
```

Wenn `RADIO_LOG_CHANNEL_ID` gesetzt ist, postet der Bot Trackwechsel und Health-Statuswechsel in diesen Kanal.

## 4. Commands registrieren

Nach jedem neuen Slash-Command:

```bash
npm run register
```

Oder Windows:

```powershell
.\start-666RadioCoreDJ.ps1 -RegisterCommands
```

## 5. Bot starten

```bash
npm start
```

Oder Windows:

```powershell
.\start-666RadioCoreDJ.ps1 -StartBot
```

## 6. Discord-Befehle

```text
/play
/play preset:1
/play preset:2
/pause
/resume
/stop
/volume
/volume level:80
/volume level:120
/volume default:true
/radio panel
/radio status
/radio skip
/radio jingle name:DEIN_JINGLE
```

## 7. SonicPanel-Daten

Echte SonicPanel-/DJ-Daten nur in `.env` eintragen. Nicht in GitHub committen.

```env
SONICPANEL_PANEL_URL=http://YOUR_PANEL_HOST:2080
SONICPANEL_DJ_USER=PASTE_DJ_USER_HERE
SONICPANEL_DJ_PASS=PASTE_DJ_PASSWORD_HERE
```

Der AutoDJ-Skip-Endpoint fehlt weiterhin, bis er im DJ-Panel-Netzwerk-Tab ermittelt oder vom Provider geliefert wurde.

## 8. Lokaler Audit

```bash
npm run check
npm run audit:local
```
