# 666 RadioBotAI — AUDIT PHASE2C23 SoundCloud Required

```text
AUDIT: PASS WITH RUNTIME REQUIREMENT
VERSION: v1.2.3
SCHWERPUNKT: SoundCloud + Lavalink
```

## Entscheidung

```text
🟢 SoundCloud ist Pflichtquelle.
🟢 Lavalink ist Pflicht-Runtime für Vocard-Musikbetrieb.
🟢 scsearch muss im Bot verfügbar sein.
🟢 Installer-/Lavalink-Config darf in die Repo.
🟡 kompletter Lavalink-Server-Quellcode bleibt extern.
🔴 YuE/Sonify werden nicht in die RadioBotAI-Kernrepo integriert.
```

## Runtime-Kette

```text
Discord User
→ /soundcloud oder /scsearch
→ RadioBotAI/Vocard Cog
→ Lavalink Node
→ SoundCloud Source/scsearch
→ Discord Voice Playback
```

## Risiko

```text
Lavalink fehlt live: Musikbetrieb FAIL
SoundCloud source deaktiviert: SoundCloud FAIL
Falsches Lavalink Passwort: Node-Verbindung FAIL
```

## Freigabe

```text
Repo-Integration: GO
Live-Test: OFFEN
Lavalink Runtime: REQUIRED
```
