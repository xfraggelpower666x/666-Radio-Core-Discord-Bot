# 666 RadioBotAI Commands

## Radio-Steuerung

```text
/radio play [stream_url] [channel]
/radio stop
/radio pause
/radio resume
/radio repair
/radio volume <0-500>
/radio nowplaying
/radio status
/radio info
```

## Konfiguration

```text
/radio setstream <url>
/radio setvoice <voice-channel>
/radio setlog <text-channel>
/radio setadminrole <role>
/radio setupadmin [member] [administrator]
/radio invite
```

## Adminlogik

Ein User darf RadioBotAI administrieren, wenn mindestens eine Bedingung stimmt:

- Discord Administrator
- Berechtigung `Server verwalten`
- ID in `bot_access_user` in `settings.json`
- gesetzte RadioBotAI-Adminrolle
- Rolle in `RADIO_ALLOWED_ROLE_IDS`

## Repair-Funktion

`/radio repair` trennt einen kaputten/stuck Player sauber, verbindet neu und lädt den konfigurierten Stream erneut. Das ist für typische Lavalink-/Voice-Reconnect-Probleme gedacht.
