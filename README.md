# 666RadioCoreDJ v1.3.0

Sauber getrennte Repo-Struktur für **Discord-Voice-Bot** und **Cloudflare Worker**.

## Kernentscheidung

Der Discord-Bot mit `/play`, `/pause`, `/resume`, `/stop`, `/volume` und Voice-Streaming läuft als **dauerhafter Node.js-Prozess** in `discord-bot/`.

Der Cloudflare Worker in `worker/` ist nur der öffentliche/API-nahe Layer für:

- `/health`
- `/nowplaying`
- `/presets`
- `/preset/1` bis `/preset/5`
- später: sichere Status-/Webhook-/Control-Brücke

Der Worker ist **nicht** der Discord-Voice-Bot.

## Repo-Struktur

```text
666RadioCoreDJ_v1_3_0/
├─ discord-bot/
│  ├─ package.json
│  ├─ src/
│  ├─ scripts/
│  ├─ .env.example
│  └─ start-666RadioCoreDJ.ps1
│
├─ worker/
│  ├─ package.json
│  ├─ wrangler.toml
│  ├─ .dev.vars.example
│  └─ src/index.js
│
├─ docs/
│  ├─ MASTER_HANDOFF.md
│  ├─ SYSTEM_OUTLINE_STAND.md
│  ├─ MODULE_REGISTRY.md
│  ├─ CODE_STRUCTURE_AUDIT.md
│  ├─ AUDIT_APPENDIX.md
│  └─ ...
│
├─ archive/
│  └─ previous-flat-radio-core-v1_0/
│
├─ .gitignore
└─ README.md
```

## Cloudflare Worker Deploy

Für Cloudflare Workers Git-Deploy:

```text
Repo: xfraggelpower666x/666-Radio-Core-Discord-Bot
Branch: Codex
Stammverzeichnis / Root directory: worker
Build-Befehl: leer
Deploy-Befehl: npx wrangler deploy
```

## Discord-Bot lokal starten

```powershell
cd discord-bot
.\start-666RadioCoreDJ.ps1 -Install
.\start-666RadioCoreDJ.ps1 -RegisterCommands
.\start-666RadioCoreDJ.ps1 -StartBot
```

Oder normal:

```bash
cd discord-bot
cp .env.example .env
npm install
npm run register
npm start
```

## Sicherheitsregel

Keine echten Discord-, DJ-, SonicPanel-, SHOUTcast- oder Webhook-Secrets in GitHub schreiben. Echte Werte gehören nur in:

- `discord-bot/.env` auf dem Bot-Host
- Cloudflare Worker Secrets / Variables
- lokale `.dev.vars` nur für Worker-Entwicklung

## Codex-Handoff

- `MANIFEST.json`
- `CHANGELOG.md`
- `docs/MASTER_HANDOFF.md`
- `docs/AUDIT_APPENDIX.md`
- `docs/GO_NO_GO.md`
- `docs/CODEX_NEXT_STEPS.md`

Der vorherige flache Codex-Bot-Stand wurde nicht gelöscht, sondern unter `archive/previous-flat-radio-core-v1_0/` historisch gesichert.
