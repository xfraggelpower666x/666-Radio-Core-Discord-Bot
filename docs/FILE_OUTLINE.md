# File Outline

## Repository Root

| Pfad | Zweck |
| --- | --- |
| `.env.example` | Platzhalter fuer lokale Env-Variablen und GitHub Secrets. |
| `.gitignore` | Schuetzt Secrets, Dependencies und lokale Artefakte vor Commit. |
| `package.json` | Node-Projekt, Runtime Dependencies und Scripts. |
| `package-lock.json` | Reproduzierbare npm Dependency-Aufloesung. |
| `README.md` | Kurzuebersicht, Features, Commands und Doc-Links. |

## Source

| Pfad | Zweck |
| --- | --- |
| `src/index.js` | Bot-Start, Discord Client, Service Wiring, Shutdown. |
| `src/deploy-commands.js` | Slash Command Deployment fuer Guild oder global. |
| `src/config/env.js` | Env-Validation, Defaultwerte, Secret-Redaction. |
| `src/commands/definitions.js` | Slash Command JSON Definitionen. |
| `src/commands/router.js` | Interaction Routing und Radio Command Handling. |
| `src/commands/app-manager.js` | Bewahrter App-Manager aus dem ZIP-Kontext. |
| `src/services/radio-core.js` | Voice Join, FFmpeg Playback, Reconnect, Status Embed. |
| `src/services/icy-metadata-reader.js` | SHOUTcast/Icecast ICY Metadata Reader. |
| `src/services/stream-health-monitor.js` | Periodischer Stream Health Check. |
| `src/services/logger.js` | Console Logging und optionaler Discord Log Channel. |
| `src/services/discord-api.js` | REST Helper fuer Guild Integrations. |
| `src/utils/track.js` | ICY Metadata Parsing und Track-Normalisierung. |

## Tests

| Pfad | Zweck |
| --- | --- |
| `tests/env.test.js` | Validiert Env-Konfiguration und Redaction. |
| `tests/track.test.js` | Validiert ICY Metadata Parsing und Track Cleanup. |

## Docs

| Pfad | Zweck |
| --- | --- |
| `docs/HANDOFF.md` | Uebergabe, Quellenstatus und Systemtrennung. |
| `docs/FILE_OUTLINE.md` | Datei-Outline dieses Projekts. |
| `docs/MODULE_REGISTER.md` | Modulregister mit Status. |
| `docs/AUDIT.md` | Audit-Anhang mit Findings und Reparaturen. |
| `docs/SETUP.md` | Lokales Setup und Bot-Rechte. |
| `docs/DEPLOY.md` | Deployment, Secrets und Rollback. |
| `docs/NEXT_STEPS.md` | Codex-Next-Steps und Owner-Nachtraege. |
