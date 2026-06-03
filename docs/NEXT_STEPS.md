# Codex Next Steps

## Sofort erledigt

- Leeren Branch in lauffaehiges Node/Discord-Projekt verwandelt.
- Radio Core Runtime implementiert.
- ZIP-App-Manager sicher als Kompatibilitaetsmodul uebernommen.
- Dokumentation und Audit-Anhang erstellt.
- Secrets aus dem Repo herausgehalten.

## Nachzutragen durch Owner

- Echter Discord Bot Token als Secret oder lokale `.env`.
- Discord `CLIENT_ID`.
- Testserver `GUILD_ID`.
- Log Channel `LOG_CHANNEL_ID`, falls gewuenscht.
- Produktiver SHOUTcast/Icecast `RADIO_STREAM_URL`.
- Inhalt der nicht auffindbaren Master-Prompt-Datei, falls dieser ueber die Nutzernachricht hinaus verbindliche Details enthaelt.

## Empfohlene naechste Codex-Pruefungen

1. Mit echten `.env` Werten `/radio play` in einem Testserver ausfuehren.
2. Einen echten Icecast-Stream mit ICY Metadata testen.
3. Einen echten SHOUTcast-Stream testen.
4. Bot fuer mehrere Guilds bewerten, falls Multi-Guild-Betrieb gewuenscht ist.
5. Optional: StreamSentinel als separates Operations-Modul oder eigenes Repo spezifizieren.
