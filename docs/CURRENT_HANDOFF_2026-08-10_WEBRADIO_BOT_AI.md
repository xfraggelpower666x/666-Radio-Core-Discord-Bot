# 666SOUNDsDESIGn WebRadio Bot AI — Preservation Handoff

**Date:** 2026-08-10
**Status:** PRESERVATION CHECKPOINT / READ-ONLY AUDIT BASIS
**Repository:** `xfraggelpower666x/666RadioBotAI`
**Production branch:** `666RadioBotAI`

## 1. Bot identity and scope

Existing Discord bot/application:

`666SOUNDsDESIGn WebRadio Bot AI`

This bot is the dedicated Discord WebRadio / stream playback bot.

It is strictly separate from the LYVRA character bot. The LYVRA character bot represents LYVRA as a character/personality and must not be repurposed as the radio-control bot.

Do not create a second Discord application for this work.

## 2. Non-destructive protection rule

Existing repository structures are to be preserved unless a later change is explicitly authorized and verified.

### HARD PRESERVE

**The existing Renderer / Render-related directory structure in this repository must NOT be deleted, replaced, merged away, renamed, or silently simplified.**

Renderer-related files/services are part of the existing RadioBotAI architecture and must remain present during RadioBotAI repair work.

Any future cleanup must treat Renderer content as protected existing architecture.

The productive WebRadio repository/core is also outside the mutation scope of the RadioBotAI repair unless an explicit separate instruction authorizes a specific WebRadio change.

## 3. Existing Cloudflare deployment

Cloudflare project:

`666radiobotai`

Verified Git integration configuration:

- repository: `xfraggelpower666x/666RadioBotAI`
- production branch: `666RadioBotAI`
- root directory: `Workers/666radiobotai`
- deploy command: `npx wrangler deploy`
- version command: `npx wrangler versions upload`

Current deploy files include:

- `Workers/666radiobotai/wrangler.toml`
- `Workers/666radiobotai/Arbeiter/src/index.js`
- `Workers/666radiobotai/package.json`

The Cloudflare project exists, but the latest visible build was reported as failed. Repair must remain scoped to RadioBotAI unless separately authorized.

## 4. Worker role

The `666radiobotai` Cloudflare Worker is NOT the Discord Voice runtime.

Its intended responsibilities include:

- API layer
- dashboard / control bridge
- status / health
- Now Playing bridge
- Discord shooter control
- Player Alert relay

Discord Voice playback with FFmpeg requires a separate persistent bot process/host.

## 5. Current Cloudflare public configuration

Current intended public values include:

- `PUBLIC_BOT_NAME = 666SOUNDsDESIGn WebRadio Bot AI`
- `PUBLIC_PROJECT_NAME = 666SOUNDsDESIGn WebRadio`
- `PUBLIC_MAIN_STREAM_URL = https://my.idjstream.com/8686/stream`
- `PUBLIC_FALLBACK_STREAM_URL = https://my.idjstream.com/666soundsdesign/stream`
- `PUBLIC_WEBRADIO_BASE_URL = https://webradio.666soundsdesign-broadcaster.com`
- `PUBLIC_TUNEIN_URL = https://tunein.com/radio/s357001`
- `PUBLIC_VERSION = v1.2.2-audit-split-real-skip`
- `PUBLIC_WORKER_ROLE = RadioBotAI API / Discord Shooter Control`

The Git `wrangler.toml` was observed to contain older public values and therefore requires controlled synchronization before a successful production redeploy.

## 6. Discord webhook replacement required

Existing Cloudflare secret names:

- `DISCORD_WEBHOOK_URL`
- `DISCORD_WEBHOOK_URL2`
- `DISCORD_WEBHOOK_URL3`

The previous Discord server was deleted and a new server exists. Therefore these three webhook secrets must be replaced with new webhook targets for the new Discord server.

Never commit webhook values, Discord bot tokens, Cloudflare API tokens, passwords, or other secret values to Git.

## 7. Player Alert / Render backend

Verified backend identity returned by the RadioBotAI backend:

`666-radiobotai-player-alert-render-backend`

Verified routes:

- `/health`
- `/api/player-alert/status`
- `/api/player-alert/send`
- `/api/player-alert/current`
- `/api/player-alert/history`

The Worker-to-Render/Renderer integration is existing architecture and must be preserved.

## 8. Metadata / Now Playing — canonical decision

Do NOT make RadioBotAI depend directly on raw SonicPanel/IDJ JSON unless a later fallback-specific requirement demands it.

The existing WebRadio worker already handles provider-specific metadata upstreams, normalization, fallback, runtime configuration and caching.

Verified WebRadio metadata upstreams:

- `https://my.idjstream.com/cp/get_info.php?p=8686`
- `http://my.idjstream.com/cp/get_info.php?p=8686`
- `https://idjstream.app/cp/get_info.php?p=8686`

SonicPanel exposes title, artwork, listeners, unique listeners, bitrate, live-DJ data and history through that JSON API and recommends polling no faster than approximately 5–10 seconds for AJAX use.

### Canonical RadioBotAI metadata source

RadioBotAI should consume the already normalized WebRadio endpoint:

`https://webradio.666soundsdesign-broadcaster.com/api/nowplaying`

Architecture:

```text
SonicPanel / IDJ JSON
        ↓
WebRadio metadata upstream / fallback / normalizer
        ↓
WebRadio /api/nowplaying
        ↓
666radiobotai Worker
        ↓
Discord Now Playing / status
```

This avoids duplicating fragile provider-specific JSON parsing in RadioBotAI.

## 9. Stream playback architecture

Current intended audio sources:

```text
MAIN
https://my.idjstream.com/8686/stream

FALLBACK
https://my.idjstream.com/666soundsdesign/stream
```

The Discord Voice runtime should ultimately provide stable 24/7 playback, reconnect handling, status, and Now Playing under the existing bot identity.

## 10. Safe repair order

1. Preserve all existing repository architecture, especially Renderer/Render-related directories.
2. Audit current `Workers/666radiobotai` files against the Cloudflare dashboard state.
3. Synchronize only verified public Worker configuration.
4. Keep secrets out of Git.
5. Repair the `666radiobotai` Cloudflare deploy.
6. Read back `/health`, `/status`, `/stream`, `/nowplaying`, `/dashboard`.
7. Replace the three Discord webhook secrets for the new Discord server.
8. Repair/verify the persistent Discord Voice runtime separately.
9. Do not modify productive WebRadio core merely to make RadioBotAI work.

## 11. Interruption-safe continuation rule

Work on RadioBotAI must be resumable without losing the active task when the user sends side remarks, corrections, screenshots, new evidence, or unrelated short interjections during an ongoing step.

Rules:

- A user interjection does **not** cancel the active task unless the user explicitly says to stop, cancel, abandon, replace, or change scope.
- Before switching attention to the interjection, keep the current task/checkpoint and unfinished substeps intact.
- After addressing the interjection, resume the interrupted task automatically from the last verified checkpoint.
- Do not silently drop queued repair/audit steps because the conversation branched temporarily.
- If new information affects the active task, integrate it and continue from the adjusted checkpoint.
- If new information conflicts with the active task, mark `CONFLICT` and pause only the conflicting substep; keep unaffected work queued.
- Never claim that an interrupted step finished if it did not.
- After any consequential write, record the resulting commit/checkpoint before continuing.

Continuation state labels:

- `ACTIVE` — currently executing task.
- `QUEUED` — already agreed follow-up work not yet completed.
- `INTERRUPTED` — temporarily displaced by a user interjection, must resume automatically.
- `RESUMED` — continued from the last verified checkpoint.
- `BLOCKED` — cannot continue without external input/access.
- `DONE` — verified completed step.

## 12. Current status labels

- `VERIFIED`: existing Discord bot identity is `666SOUNDsDESIGn WebRadio Bot AI`.
- `VERIFIED`: Cloudflare Git deploy target is `Workers/666radiobotai` on branch `666RadioBotAI`.
- `VERIFIED`: WebRadio already implements robust metadata upstream/fallback architecture.
- `VERIFIED`: the dedicated RadioBotAI Player Alert Render backend exists and responds with its route set.
- `REQUIRED`: three Discord webhook secrets must be replaced because the previous Discord server was deleted.
- `CONFLICT`: current Cloudflare public values and repository `wrangler.toml` are not fully synchronized.
- `PROTECTED`: Renderer / Render-related repository directories and files must remain intact.
- `OUT_OF_SCOPE`: destructive or unrelated changes to the productive WebRadio system.
- `CONTINUATION_REQUIRED`: side remarks/interjections must not cause active or queued RadioBotAI work to be lost.
