# Module Registry

MOD-001 DISCORD BOT CORE: BESTAETIGT, discord-bot/index.js, discord-bot/src/index.js, Node.js Gateway runtime, not Worker.
MOD-002 SLASH COMMAND REGISTRY: BESTAETIGT, discord-bot/src/discord/commands.js, discord-bot/scripts/register-commands.js.
MOD-003 DISCORD APP / INTEGRATION MANAGER: HISTORISCH, archived under archive/previous-flat-radio-core-v1_0/.
MOD-004 DISCORD SECURITY GATE: BESTAETIGT, discord-bot/src/discord/permissions.js.
MOD-005 RADIO CORE: BESTAETIGT, discord-bot/src/voice/voiceRelay.js.
MOD-006 STREAM STATUS ENGINE: BESTAETIGT / config-dependent, discord-bot/src/radio/streamHealthMonitor.js plus Worker status routes.
MOD-007 NOWPLAYING ENGINE: BESTAETIGT / config-dependent, discord-bot/src/radio/icyMetadataReader.js for ICY StreamTitle and worker/src/index.js for public nowplaying route.
MOD-008 LISTENER COUNT ENGINE: GEPLANT / UNBEKANNT.
MOD-009 AUTODJ CONTROL: VORBEREITET / OFFEN, SonicPanel endpoints missing.
MOD-010 WEBHOOK POSTING LAYER: GEPLANT / NOT ACTIVE.
MOD-011 CLOUDFLARE WORKER API: BESTAETIGT, worker/.
MOD-012 WORKER HEALTH ROUTE: BESTAETIGT, GET /health.
MOD-013 REMOTE CONTROL API: GEPLANT / NOT ACTIVE.
MOD-014 GITHUB DEPLOY CONTEXT: BESTAETIGT, branch Codex.
MOD-015 CLOUDFLARE DEPLOY CONTEXT: BESTAETIGT / dashboard check required.
MOD-016 SECRET GOVERNANCE: BESTAETIGT, no secret values in repo.
MOD-017 AUDIT / TEST SYSTEM: PASS, local checks completed.
MOD-018 ICY METADATA READER: BESTAETIGT, discord-bot/src/radio/icyMetadataReader.js.
MOD-019 TRACK CHANGE DETECTION: BESTAETIGT, discord-bot/src/utils/track.js and voiceRelay event binding.
MOD-020 DISCORD LOG CHANNEL SUPPORT: BESTAETIGT / config-dependent, RADIO_LOG_CHANNEL_ID.
MOD-021 GITHUB RADIO CORE CI: BESTAETIGT, .github/workflows/ci.yml.
