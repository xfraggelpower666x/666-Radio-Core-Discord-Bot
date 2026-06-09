# 666 RadioBotAI

**666 RadioBotAI** ist ein Discord Voice Radio Bot für den **666SOUNDsDESIGn WebRadio** Stream.

Die Basis ist die vorhandene Vocard/Voicelink-Playback-Architektur. Sie wurde nicht destruktiv ersetzt, sondern um eine eigene RadioBotAI-Steuerschicht erweitert.

## Hauptfunktion

Der Bot verbindet sich mit einem Discord-Voice-Channel und spielt einen konfigurierten WebRadio-Stream ab.

## Wichtigste Commands

| Command | Funktion |
|---|---|
| `/radio play` | startet den konfigurierten Stream |
| `/radio stop` | stoppt den Stream und trennt den Bot |
| `/radio pause` | pausiert die Wiedergabe |
| `/radio resume` | setzt die Wiedergabe fort |
| `/radio volume <0-500>` | setzt die Lautstärke |
| `/radio nowplaying` | zeigt aktuell geladenen Stream/Track |
| `/radio status` | zeigt Verbindung, Stream, Voice, Admin-Rolle |
| `/radio repair` | verbindet neu und lädt den Stream erneut |
| `/radio setstream <url>` | speichert die Stream-URL pro Discord-Server |
| `/radio setvoice <channel>` | speichert den Standard-Voice-Channel |
| `/radio setlog <channel>` | speichert den Log-Textchannel |
| `/radio setadminrole <role>` | registriert eine vorhandene Radio-Adminrolle |
| `/radio setupadmin` | erstellt/registriert die RadioBotAI-Adminrolle |
| `/radio invite` | erzeugt Invite-Links mit Radio-Rechten oder Volladmin |
| `/radio info` | zeigt die Bot-Projektinformation |

## Docker-Start

```bash
cp .env.example .env
# .env bearbeiten: DISCORD_TOKEN, DISCORD_CLIENT_ID, RADIO_STREAM_URL setzen

docker compose up -d --build
```

Die Compose-Datei startet:

- `bot` = 666 RadioBotAI
- `lavalink` = Audio-/Stream-Node
- `mongo` = Server-/Admin-/Radio-Konfiguration

## Konfiguration

Die wichtigsten Werte stehen in `.env`:

```env
DISCORD_TOKEN=...
DISCORD_CLIENT_ID=...
RADIO_STREAM_URL=https://...
RADIO_VOICE_CHANNEL_ID=0
RADIO_LOG_TEXT_CHANNEL_ID=0
RADIO_ADMIN_ROLE_ID=0
RADIO_DEFAULT_VOLUME=80
```

Alternativ kann vieles direkt über Discord gesetzt werden:

```text
/radio setstream <stream-url>
/radio setvoice <voice-channel>
/radio setlog <text-channel>
/radio setupadmin
```

## Hinweise

- Secrets niemals in öffentliche Dateien schreiben.
- `settings.json` enthält keine echten Zugangsdaten und zieht Token bevorzugt aus `.env`.
- Lavalink ist Pflicht, weil die vorhandene Voicelink-Engine darüber Audio in Discord ausgibt.
- MongoDB ist Pflicht für Server-Konfigurationen und Command-Settings.
- Die ursprüngliche MIT-Lizenz der Vocard-Basis bleibt erhalten.

Weitere Details: `docs/SETUP.md`, `docs/COMMANDS.md`, `docs/CHANGELOG.md`.
