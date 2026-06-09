# Changelog

## v666-radiobotai-1.0.0

### Geändert

- Vocard-Basis zu **666 RadioBotAI** umgebaut.
- Bot-Klasse in `RadioBotAI` umbenannt.
- Startup-Branding und Logs auf RadioBotAI angepasst.
- Externer Vocard-Updatecheck standardmäßig deaktiviert.

### Ergänzt

- Neue Datei `cogs/radio.py` mit `/radio` Command-Gruppe.
- Stream starten/stoppen/pausieren/fortsetzen.
- Stream-Repair durch Neuverbinden und Reload.
- Volume-Control 0-500.
- Now Playing und Status-Anzeige.
- Stream-/Voice-/Log-Channel pro Server speicherbar.
- RadioBotAI-Adminrolle setzbar oder automatisch erstellbar.
- Invite-Command mit empfohlenen Radio-Rechten und Volladmin-Link.
- Info-Command mit Bot-Projektbeschreibung.
- Controller-Info-Button `radioinfo` ergänzt.
- Docker Compose mit Bot, Lavalink und MongoDB.
- `.env.example`, `settings.example.json`, `lavalink/application.yml`.

### Erhalten

- Vocard/Voicelink Playback-Engine.
- Lavalink-Anbindung.
- MongoDB-Settings.
- Bestehende Music-/Playback-Commands bleiben verfügbar.
- MIT-Lizenz der Originalbasis bleibt erhalten.

### Sicherheit

- Keine echten Secrets eingetragen.
- Token werden über `.env` geladen.
- Query-Parameter von Stream-URLs werden in Statusanzeigen nicht vollständig ausgegeben.
