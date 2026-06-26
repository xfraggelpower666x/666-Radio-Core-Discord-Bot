# 666SOUNDsDESIGn RadioBotAI HYBRID v3.3.0

Zusammengeführter Discord-Voice-Bot aus beiden gelieferten Projekten:

- stabiler 24/7-Webradio-Streambot
- lokale AutoDJ-/Musikbibliotheks-Engine mit SQLite, Scanner, Queue und Suche
- geschütztes `/skip` über Cloudflare RadioBotAI Worker
- optionaler Admin-Worker- und direkter SHOUTcast-Fallback
- fünf vorkonfigurierte Stream-Presets
- `/home` für WebRadio und RadioBotAI-Dashboard
- Healthcheck für HeavenCloud, Docker und Prozessmanager
- geschütztes `/radioalert` über Cloudflare Worker zum Render Alert-Service
- `/alertstatus`, `/alertcurrent` und `/alerthistory` für Backendprüfung

## Presets

```text
1  https://my.idjstream.com/666soundsdesign/stream
2  https://my.idjstream.com:8686
3  https://my.idjstream.com:8686/stream
4  https://tunein.com/embed/player/s357001/
5  Lokaler AutoDJ aus ./music
```

Preset 4 ist ein Browser-Link und kein direkter FFmpeg-Audiostream.

## Zentrale Commands

```text
/play          Webradio starten
/presets       alle fünf Presets anzeigen
/preset        Preset 1-5 aktivieren
/autodj        lokalen AutoDJ aktivieren
/track         lokalen Titel suchen/einreihen
/skip          lokalen Titel oder Remote-AutoDJ überspringen
/skipstatus    geschützte Worker-Bridge prüfen
/radioalert    Nachricht an den WebRadio Player-Alert-Service senden
/alertstatus    Worker/Render/KV-Verbindung prüfen
/alertcurrent   aktuell gespeicherten Alert anzeigen
/alerthistory   Alert-Historie anzeigen
/home          WebRadio und Dashboard öffnen
/status        Bot-, Voice-, Worker- und Healthstatus
/stop          Wiedergabe stoppen und Voice trennen
```

## 24/7 Schnellstart

```bash
cp .env.example .env
# .env sicher ausfüllen
pip install -r requirements.txt
python scripts/selftest.py
./start.sh
```

Docker:

```bash
docker compose up -d --build
```

PM2:

```bash
pm2 start ecosystem.config.cjs
pm2 save
```

HeavenCloud: siehe `heavencloud/STARTUP.md`.

## Sicherheit

- Keine Tokens, Passwörter oder Webhooks im Quellcode.
- `.env` bleibt lokal und ist durch `.gitignore` ausgeschlossen.
- Der direkte Admin-Worker-Fallback ist standardmäßig deaktiviert.
- Direkter SHOUTcast-`kicksrc` ist nur eine optionale Notfallroute.
