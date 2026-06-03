# 666SOUNDsDESIGn Radio Core Discord Bot

Modern Discord radio bot for **666-Radio-Core-Discord-Bot**.

This repository separates the systems strictly:

- **666SOUNDsDESIGn AI**: creative system, not implemented here.
- **StreamSentinel**: community and operations layer, documented as adjacent scope.
- **Radio Core**: broadcast and radio technology implemented in this bot.

## Features

- Discord.js v14 slash commands
- Discord voice channel radio playback
- SHOUTcast and Icecast stream support through FFmpeg
- ICY metadata reader
- auto reconnect and replay
- stream health monitoring
- track change detection
- broadcast status embeds
- optional log channel support
- `.env` / GitHub Secrets workflow without committed secrets
- handoff, audit, setup and deploy documentation

## Quick Start

```bash
npm install
copy .env.example .env
npm run deploy:commands
npm start
```

Fill `.env` before deploying commands or starting the bot.

## Slash Commands

- `/radio play [stream_url] [station_name]`
- `/radio stop`
- `/radio status`
- `/radio reconnect`
- `/radio nowplaying`
- `/apps-list`
- `/apps-remove integration_id:<id> confirm:<true>`

The `/apps-*` commands preserve the uploaded App Manager Bot seed as a guarded admin compatibility module.

## Documentation

- [Handoff](docs/HANDOFF.md)
- [File Outline](docs/FILE_OUTLINE.md)
- [Audit](docs/AUDIT.md)
- [Setup](docs/SETUP.md)
- [Deploy](docs/DEPLOY.md)
- [Module Register](docs/MODULE_REGISTER.md)
- [Codex Next Steps](docs/NEXT_STEPS.md)
