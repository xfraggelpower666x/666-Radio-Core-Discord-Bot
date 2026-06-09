# 666 RadioBotAI Setup

## 1. Discord Application vorbereiten

1. Discord Developer Portal öffnen.
2. Bot/Application erstellen.
3. Bot Token erzeugen und nur lokal in `.env` speichern.
4. Privileged Gateway Intents prüfen:
   - Message Content nur nötig, wenn Prefix-Commands aktiv genutzt werden.
   - Voice State Intent ist im Code aktiv.

## 2. ENV anlegen

```bash
cp .env.example .env
```

Dann `.env` bearbeiten:

```env
DISCORD_TOKEN=DEIN_TOKEN
DISCORD_CLIENT_ID=DEINE_CLIENT_ID
RADIO_STREAM_URL=https://dein-stream.example/stream
RADIO_VOICE_CHANNEL_ID=0
RADIO_LOG_TEXT_CHANNEL_ID=0
RADIO_DEFAULT_VOLUME=80
```

`RADIO_VOICE_CHANNEL_ID=0` bedeutet: `/radio play` nutzt den Voice-Channel des Users, der den Command ausführt.

## 3. Docker starten

```bash
docker compose up -d --build
```

Logs prüfen:

```bash
docker compose logs -f bot
```

## 4. Slash Commands synchronisieren

Beim ersten Start synchronisiert der Bot die Slash Commands selbst, sobald `settings.json`/Version passt.
Wenn Commands nicht sofort erscheinen, Discord kurz warten lassen oder Bot neu starten:

```bash
docker compose restart bot
```

## 5. Admin-Rolle einrichten

In Discord:

```text
/radio setupadmin
```

Optional mit Volladmin-Rolle:

```text
/radio setupadmin administrator:true
```

Sicherer Standard ist `administrator:false`. Dann ist die Rolle eine Bot-interne Radio-Adminrolle und bekommt nicht automatisch Discord-Volladminrechte.

## 6. Stream setzen

```text
/radio setstream https://dein-stream.example/stream
/radio play
```

## 7. Bot einladen

In Discord:

```text
/radio invite
```

Der Command liefert zwei Links:

- empfohlene Radio-Rechte
- Volladmin-Invite

## Prefix-Commands

`settings.json` setzt `prefix` standardmäßig auf `null`. Dadurch wird kein Message-Content-Intent benötigt und der Bot arbeitet primär mit Slash Commands.
Wenn Prefix-Commands wie `?play` gewünscht sind, `prefix` wieder auf `?` setzen und Message Content Intent im Discord Developer Portal aktivieren.

## Windows Schnellstart

```text
START_RADIOBOTAI_DOCKER.bat
CHECK_RADIOBOTAI_LOGS.bat
STOP_RADIOBOTAI_DOCKER.bat
```

Beim ersten Start erzeugt `START_RADIOBOTAI_DOCKER.bat` aus `.env.example` eine `.env` Vorlage und stoppt, damit Token und Stream sauber eingetragen werden können.
