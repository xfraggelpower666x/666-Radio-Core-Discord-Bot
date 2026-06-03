# Code Structure Audit

## File Overview

| Pfad | Typ | Rolle | Status | Risiko | Notiz |
|---|---|---|---|---|---|
| discord-bot/ | Node app | Discord Bot runtime | PASS | Medium | Needs 24/7 host and env secrets. |
| worker/ | Cloudflare Worker | Public API | PASS | Medium | Dashboard Root Directory must be worker. |
| docs/ | Markdown | Handoff/audit | PASS | Low | Unknowns marked. |
| archive/previous-flat-radio-core-v1_0/ | Archive | Prior flat implementation | HISTORISCH | Low | Preserved, not active. |

## Entrypoints

Bot: discord-bot/index.js; Runtime: discord-bot/src/index.js; Commands: discord-bot/scripts/register-commands.js; Worker: worker/src/index.js.

## Checks

Bot install PASS. Bot syntax PASS. Bot local audit PASS. Worker install PASS. Worker syntax PASS. Secret scan PASS.
