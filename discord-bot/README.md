# 666RadioCoreDJ

> Hinweis v1.3.0: Dieses Verzeichnis ist nur der Discord-Bot. Der Cloudflare Worker liegt separat in `../worker/`. Für Bot-Start immer zuerst in `discord-bot/` wechseln.


Umbau des hochgeladenen `discobot-master` zu einem modularen **666RadioCoreDJ** für Discord → SonicPanel/MyIDJ Radio-Control plus Discord-Voice-Stream.

## Ziel

Der Bot stellt aus Discord heraus diese Aktionen bereit:

- `/play` → startet den Default-Stream im Voice-Channel, in dem der User gerade ist
- `/play preset:1-5` → startet gezielt einen der bis zu 5 konfigurierten Stream-Presets
- `/pause` → pausiert den Voice-Stream, Bot bleibt im Channel
- `/resume` → setzt den pausierten Voice-Stream live fort
- `/stop` → stoppt den Voice-Stream und trennt den Bot vom Voice-Channel
- `/volume` → zeigt aktuelle Lautstärke
- `/volume level:<0-200>` → setzt die Voice-Lautstärke in Prozent
- `/volume default:true` → setzt auf `VOICE_DEFAULT_VOLUME_PERCENT` zurück
- `/radio skip` → AutoDJ aktuellen Track überspringen, sobald der echte SonicPanel-Request bekannt ist
- `/radio status` → Konfiguration ohne Secrets prüfen
- `/radio panel` → Button-Panel posten
- `/radio jingle <name>` → vorbereiteter Jingle/ID On-Air, sobald der echte SonicPanel-Request bekannt ist

## Wichtige Sicherheitsregel

Echte Zugangsdaten gehören ausschließlich in `.env` auf dem Zielsystem.

Nicht in:

- GitHub
- Discord-Nachrichten
- Screenshots
- `README.md`
- `.js`-Dateien
- `.env.example`

## Status dieses Builds

Der Discord-Bot, Rechteprüfung, Cooldowns, Panel, Slash Commands, SonicPanel-Adapter, Jingle-Adapter, SHOUTcast-Fallback und Voice-Stream sind eingebaut.

Neu in v1.3.0: Repo-Trennung. Bot liegt jetzt unter `discord-bot/`, Worker unter `worker/`. Die v1.2.0-Voice-Funktionen bleiben vollständig erhalten.

Weiterhin enthalten:

- 5 Stream-Presets
- Default-Preset
- Pause/Resume
- Stop bleibt erhalten
- Lautstärkeregelung mit Default-Option
- Panel-Buttons für Presets 1-5
- Panel-Button für Default-Volume
- Secret-Scan erweitert

Der echte SonicPanel-Skip kann erst funktionieren, wenn einer dieser Werte bekannt ist:

```env
SONICPANEL_SKIP_URL=
SONICPANEL_SKIP_METHOD=POST
SONICPANEL_SKIP_AUTH=none
```

Diese URL muss aus dem DJ-Panel-Netzwerk-Tab oder vom Provider kommen. SonicPanel zeigt zwar das Recht „Lied überspringen AutoDJ“, veröffentlicht aber nicht automatisch in diesem Paket den konkreten internen Button-Endpoint.

## Discord-Voice-Stream mit `/play`

Der Bot streamt den in `.env` gesetzten Radiostream in den Voice-Channel des Users.

Ablauf im Discord:

1. User geht in einen Voice-Channel.
2. User schreibt `/play` oder `/play preset:1`.
3. Bot joint diesen Voice-Channel.
4. Bot spielt den Radiostream.
5. Mit `/pause` wird die Ausgabe angehalten, ohne den Channel zu verlassen.
6. Mit `/resume` wird wieder live gestartet.
7. Mit `/stop` wird der Stream getrennt.

Der Bot benötigt auf Discord:

- View Channel
- Connect
- Speak
- Use Application Commands

Für `/play` wird zusätzlich der Gateway Intent `GuildVoiceStates` im Code genutzt.

## Stream-Presets

Bis zu 5 Streams werden über `.env` gesetzt:

```env
VOICE_DEFAULT_PRESET=1
VOICE_DEFAULT_VOLUME_PERCENT=80
VOICE_MAX_VOLUME_PERCENT=200

STREAM_PRESET_1_NAME=Main Radio
STREAM_PRESET_1_URL=http://YOUR_STREAM_HOST:PORT/stream
STREAM_PRESET_1_VOLUME_PERCENT=80

STREAM_PRESET_2_NAME=Backup Stream
STREAM_PRESET_2_URL=
STREAM_PRESET_2_VOLUME_PERCENT=80
```

Wenn kein Preset gesetzt ist, nutzt der Bot als Fallback:

```env
RADIO_STREAM_URL=http://YOUR_STREAM_HOST:PORT/stream
```

## Lautstärke

```text
/volume
/volume level:80
/volume level:120
/volume default:true
```

Die Lautstärke wirkt nur auf den Discord-Voice-Output des Bots, nicht auf SonicPanel selbst.

## Schnellstart Windows

```powershell
cd 666RadioCoreDJ
.\start-666RadioCoreDJ.ps1
```

Beim ersten Start wird `.env` aus `.env.example` erzeugt.

Dann `.env` bearbeiten und danach:

```powershell
.\start-666RadioCoreDJ.ps1 -Install
.\start-666RadioCoreDJ.ps1 -RegisterCommands
.\start-666RadioCoreDJ.ps1 -StartBot
```

## Schnellstart normal

```bash
cp .env.example .env
npm install
npm run register
npm start
```

Nach Command-Änderungen immer neu registrieren:

```bash
npm run register
```

## Discord-Rechte

Wenn `ALLOWED_ROLE_IDS` gesetzt ist, dürfen nur diese Rollen steuern.

Wenn `ALLOWED_ROLE_IDS` leer ist, greift ein Sicherheitsfallback: Nur Mitglieder mit `Manage Server` dürfen Radio-Control und Voice-Control nutzen.

Optional kann der Bot auf einen Kanal begrenzt werden:

```env
RADIO_TEXT_CHANNEL_ID=...
```

## SonicPanel-Service-Account

Empfohlene Rechte für den DJ-Service-Account:

| Recht | Wert |
|---|---:|
| DJ kann Musik streamen | Nein |
| DJ kann eigenes Passwort ändern | Nein |
| DJ kann Profilbild hochladen | Nein |
| DJ kann im DJ Panel einloggen | Ja |
| DJ kann Radio starten/stoppen | Nein |
| DJ kann AutoDJ starten/stoppen | Nein |
| DJ kann Jingles/IDs spielen | Ja, wenn Discord-Jingles gewollt |
| DJ kann Voice Pro verwenden | Nein |
| DJ kann Lied überspringen verwenden AutoDJ | Ja |

## SHOUTcast-Fallback

Der SHOUTcast-Fallback ist bewusst optional:

```env
RADIO_SKIP_FALLBACK=shoutcast_kicksrc
```

Das kickt nur die Source. Es ist kein sauberer AutoDJ-Skip. Hauptweg bleibt SonicPanel-DJ-Skip.

## Optionaler Auto-Voice-Relay

Zusätzlich zu `/play` kann der Bot beim Start automatisch in einen festen Voice-Channel gehen:

```env
VOICE_RELAY_ENABLED=true
VOICE_CHANNEL_ID=...
VOICE_DEFAULT_PRESET=1
```

Standardmäßig ist Auto-Relay deaktiviert. `/play` funktioniert trotzdem, sobald `RADIO_STREAM_URL` oder mindestens ein `STREAM_PRESET_X_URL` gesetzt ist.
