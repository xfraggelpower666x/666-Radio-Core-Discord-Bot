# Deploy

## GitHub Secrets

Keine Secrets im Repository speichern. Fuer CI/CD oder Hosting als Secrets hinterlegen:

- `DISCORD_TOKEN`
- `CLIENT_ID`
- `GUILD_ID` optional
- `LOG_CHANNEL_ID` optional
- `RADIO_STREAM_URL`
- `RADIO_STATION_NAME`

## VPS / Server

```bash
git clone https://github.com/xfraggelpower666x/666-Radio-Core-Discord-Bot.git
cd 666-Radio-Core-Discord-Bot
git checkout Codex
npm ci
npm run deploy:commands
npm start
```

Fuer dauerhaften Betrieb kann ein Prozessmanager genutzt werden, z. B. systemd oder PM2.

## systemd Beispiel

```ini
[Unit]
Description=666SOUNDsDESIGn Radio Core Discord Bot
After=network-online.target

[Service]
WorkingDirectory=/opt/666-Radio-Core-Discord-Bot
EnvironmentFile=/opt/666-Radio-Core-Discord-Bot/.env
ExecStart=/usr/bin/node src/index.js
Restart=always
RestartSec=10
User=radio-core

[Install]
WantedBy=multi-user.target
```

## Deploy Audit

Vor produktivem Start:

```bash
npm test
npm audit --omit=dev
npm run deploy:commands
```

## Rollback

Bei Problemen:

```bash
git log --oneline -5
git checkout <bekannter-guter-commit>
npm ci
npm start
```
