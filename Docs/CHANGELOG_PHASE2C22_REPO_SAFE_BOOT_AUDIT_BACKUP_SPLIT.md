# CHANGELOG PHASE2C22

## Änderungen

- aktuelle heruntergeladene Repo als Basis genommen
- Real-Skip-Zweitworker `Workers/666myidjstreamadmin` wieder integriert
- Hauptworker um AutoDJ-Forward-Routen ergänzt
- Discord-Audit-Cog und Audit-Service integriert
- AI-Cog, AI-Client und Addons wiederhergestellt
- Audit-Service auf neue Split-Logik korrigiert:
  - Bootsystem extern, nicht Repo
  - Backup-System extern, nicht Repo
  - Audit Runtime im Bot erlaubt
- keine Full-Backup-ZIP und kein Bootloader-Paket in die Repo gelegt
- Playlist On-the-Fly bleibt HOLD, kein SonicPanel-Trick

## Neue/aktive Endpunkte

```text
GET  /radio/autodj/status
POST /radio/autodj/skip
POST /api/radio/skip
POST /autodj/skip
POST /radio/autodj/playlist   -> HOLD, bis echter Endpoint bekannt
```
