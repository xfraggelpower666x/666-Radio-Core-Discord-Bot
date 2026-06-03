# Setup

## Voraussetzungen

- Node.js 20 oder neuer
- Discord Bot Application
- Bot Token als lokale `.env` Variable oder GitHub Secret
- Voice Channel im Zielserver
- HTTP(S) SHOUTcast oder Icecast Stream URL

## Lokales Setup

```bash
npm install
copy .env.example .env
```

Danach `.env` ausfuellen:

```env
DISCORD_TOKEN=...
CLIENT_ID=...
GUILD_ID=...
LOG_CHANNEL_ID=...
RADIO_STREAM_URL=https://...
RADIO_STATION_NAME=666SOUNDsDESIGn Radio Core
```

## Discord Bot Permissions

Der Bot braucht:

- View Channel
- Send Messages
- Embed Links
- Connect
- Speak
- Use Slash Commands

Fuer `/apps-list` und `/apps-remove` braucht der ausfuehrende Nutzer `Manage Server`.

## Slash Commands deployen

Testserver:

```bash
npm run deploy:commands
```

Wenn `GUILD_ID` gesetzt ist, werden Guild Commands registriert. Ohne `GUILD_ID` werden globale Commands registriert.

## Start

```bash
npm start
```

## Betrieb

1. In einen Voice Channel gehen.
2. `/radio play` ausfuehren.
3. Mit `/radio status` Broadcast- und Health-Status pruefen.
4. Mit `/radio nowplaying` den letzten ICY Track anzeigen.
5. Mit `/radio reconnect` manuell neu verbinden.
6. Mit `/radio stop` stoppen.
