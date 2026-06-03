# Module Register

## Runtime

| Modul | Zweck | Status |
| --- | --- | --- |
| `src/index.js` | Bot-Entrypoint, Client, Services, Shutdown | AKTIV |
| `src/config/env.js` | `.env` Validierung und Secret-Redaction | AKTIV |
| `src/deploy-commands.js` | Slash Command Deployment | AKTIV |

## Commands

| Modul | Zweck | Status |
| --- | --- | --- |
| `src/commands/definitions.js` | Slash Command Definitionen | AKTIV |
| `src/commands/router.js` | Interaction Routing fuer `/radio` und App-Manager | AKTIV |
| `src/commands/app-manager.js` | Erhaltener ZIP-Kontext fuer `/apps-*` | AKTIV |

## Radio Core

| Modul | Zweck | Status |
| --- | --- | --- |
| `src/services/radio-core.js` | Voice Join, FFmpeg Playback, Reconnect, Status | AKTIV |
| `src/services/icy-metadata-reader.js` | ICY Header/Metadata/Track-Change Reader | AKTIV |
| `src/services/stream-health-monitor.js` | Periodische Stream-Erreichbarkeit | AKTIV |
| `src/services/logger.js` | Console und optionaler Discord Log Channel | AKTIV |
| `src/services/discord-api.js` | Minimaler Discord REST Client fuer App-Manager | AKTIV |
| `src/utils/track.js` | ICY Metadata Parsing und Track-Normalisierung | AKTIV |

## Tests

| Modul | Zweck | Status |
| --- | --- | --- |
| `tests/track.test.js` | ICY Parsing und Track-Normalisierung | AKTIV |
| `tests/env.test.js` | Env-Validation und Redaction | AKTIV |

## Dokumentation

| Datei | Zweck | Status |
| --- | --- | --- |
| `docs/HANDOFF.md` | Handoff und Quellenstatus | AKTIV |
| `docs/AUDIT.md` | Audit-Anhang mit Findings | AKTIV |
| `docs/SETUP.md` | Lokales Setup | AKTIV |
| `docs/DEPLOY.md` | GitHub/VPS/Host Deploy | AKTIV |
| `docs/NEXT_STEPS.md` | Codex Next Steps | AKTIV |
