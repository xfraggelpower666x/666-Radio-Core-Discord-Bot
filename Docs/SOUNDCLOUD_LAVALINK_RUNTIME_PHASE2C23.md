# 666 RadioBotAI — SoundCloud / Lavalink Runtime

```text
STATUS: REQUIRED
PHASE: 2C23
VERSION: v1.2.3
ENTSCHEIDUNG: SoundCloud ist Pflichtquelle für den Radiobot-DJ.
```

## Kernentscheidung

SoundCloud läuft bei Vocard nicht zwingend als sichtbarer Einzel-Plugin-Ordner, sondern über Lavalink/Lavaplayer-Suche.

```text
SoundCloud Search Prefix: scsearch:
Lavalink Source: soundcloud: true
```

## Warum Lavalink Pflicht ist

Vocard ist ein Discord-Musikbot-Kern. Der eigentliche Audioabruf und die Plattformauflösung laufen über Lavalink-Nodes.

Ohne Lavalink:

```text
- kein stabiler Musikbetrieb
- keine SoundCloud-Suche über scsearch
- keine normale Vocard-Audio-Pipeline
```

## Runtime-Pflicht

```text
✅ Vocard Bot
✅ Lavalink Server 4+
✅ settings.json mit Lavalink Node
✅ SoundCloud Source aktiv
```

## Nicht in die Repo kippen

```text
❌ kompletter Lavalink-Server-Quellcode
❌ kompletter YuE-Code
❌ komplettes Sonify-Lab
```

## In die Repo gehört

```text
✅ Bot-Anbindung
✅ SoundCloud Cog / Commands
✅ Lavalink Config Template
✅ Installer-/Compose-Unterlagen
✅ Runtime-Dokumentation
✅ Audit-Regeln
```

## Beispiel Suche

```text
scsearch:666SOUNDsDESIGn Dark Techno
```

## Priorität

```text
1. SoundCloud
2. YouTube / YouTube Music
3. weitere LavaSrc Quellen, falls aktiv
4. Radio-/Stream-Funktionen
```
