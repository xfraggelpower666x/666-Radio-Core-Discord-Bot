# SYSTEM HANDOFF · 666SOUNDsDESIGn RadioBotAI HYBRID v3.3.0

## Status

- Hybrid-Webradio-/Local-AutoDJ-Bot: integriert
- 24/7-HeavenCloud-Profil: integriert
- `/skip` Worker-/Admin-Bridge: integriert
- fünf Stream-Presets: integriert
- `/home`: integriert
- WebRadio Player-Alert/Messenger: integriert
- Secrets im Release: keine

## Neue Player-Alert-Befehle

```text
/radioalert     geschützte Nachricht an den WebRadio-Player senden
/alertstatus    Cloudflare Worker, Render Backend und KV prüfen
/alertcurrent   aktuell gespeicherten Alert anzeigen
/alerthistory   letzte Alerts anzeigen
```

## Nachrichtenweg

```text
Discord /radioalert
    -> 666 RadioBotAI auf HeavenCloud
    -> https://666radiobotai.666soundsdesign-broadcaster.com/api/player-alert/send
    -> Render Alert Service
    -> KV-/Cache-Fallback des Workers
```

Optional kann ein direkter Render-Fallback aktiviert werden. Er bleibt standardmäßig deaktiviert.

## HeavenCloud

Das Release muss so entpackt werden, dass `main.py`, `requirements.txt`, `.env.example`, `music/`, `db/` und `botconfig/` direkt unter `/home/container/` liegen.

Bei manuellem Upload:

```text
USER UPLOADED FILES = True
AUTO UPDATE = False
APP PY FILE = main.py
```

Bei GitHub-Deployment muss zuerst exakt dieses Release in das konfigurierte Repository übertragen werden. Sonst startet HeavenCloud weiterhin den alten Repository-Stand.

## Pflicht-Secrets

```text
DISCORD_TOKEN
DISCORD_OWNER_ID
DISCORD_GUILD_ID
RADIO_VOICE_CHANNEL_ID
RADIOBOTAI_WORKER_TOKEN
```

Ohne separate Alert-Konfiguration verwendet der Bot für `/radioalert` automatisch `RADIOBOTAI_WORKER_TOKEN`.
