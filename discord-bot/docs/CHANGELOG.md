# 666RadioCoreDJ Changelog

## v1.3.0 - 2026-06-03

### Ergänzt

- `/pause` zum Pausieren des Voice-Streams ohne Channel-Disconnect.
- `/resume` zum erneuten Live-Fortsetzen nach Pause.
- `/volume` zum Anzeigen der aktuellen Lautstärke.
- `/volume level:<0-200>` zum Setzen der Discord-Voice-Lautstärke.
- `/volume default:true` zum Zurücksetzen auf `VOICE_DEFAULT_VOLUME_PERCENT`.
- `/play preset:1-5` für bis zu fünf Stream-Presets.
- Panel-Buttons für Preset 1 bis Preset 5.
- Panel-Buttons für Pause, Resume, Stop und Default-Volume.
- ENV-Konfiguration für `STREAM_PRESET_1_*` bis `STREAM_PRESET_5_*`.
- Default-Preset über `VOICE_DEFAULT_PRESET`.
- Default-Volume über `VOICE_DEFAULT_VOLUME_PERCENT`.
- Maximale erlaubte Voice-Lautstärke über `VOICE_MAX_VOLUME_PERCENT`.
- Lokaler Audit prüft jetzt zusätzliche Voice-Funktionen und bekannte Secret-Muster.

### Geändert

- Voice-Stream verwendet jetzt `inlineVolume: true`, damit Lautstärke live gesetzt werden kann.
- Pause killt FFmpeg und hält die Voice-Verbindung offen; Resume startet den Live-Stream frisch, damit kein alter Buffer abgespielt wird.
- `.env.example` wurde neutralisiert: keine echten DJ-/Stream-Zugangsdaten in der Vorlage.

### Sicherheit

- Hochgeladene DJ-Login-Daten wurden nicht in öffentliche Projektdateien übernommen.
- Keine echten Passwörter in `.env.example`, README, Docs oder JS-Code.

## v1.1.0 - 2026-06-03

### Ergänzt

- `/play` für Discord-Voice-Stream.
- `/stop` für Voice-Stream-Stop und Disconnect.
- FFmpeg-Voice-Relay über `@discordjs/voice`.
- Panel-Buttons für Voice Play und Voice Stop.

## v1.0.0 - 2026-06-03

### Initial

- Umbau von `discobot-master` zu `666RadioCoreDJ`.
- `/radio panel`, `/radio status`, `/radio skip`, `/radio jingle <name>`.
- SonicPanel/MyIDJ Adapter vorbereitet.
- SHOUTcast-Fallback vorbereitet.
- Rollen-/Channel-Gate und Cooldowns.
