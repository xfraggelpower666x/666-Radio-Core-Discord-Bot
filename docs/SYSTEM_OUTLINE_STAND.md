# System Outline Stand

| Layer-ID | Layer-Name | Zweck | Nicht-Zweck | Pfade | Status |
|---|---|---|---|---|---|
| 00 | PROJECT_IDENTITY | project identity | runtime secrets | README, MANIFEST | BESTAETIGT |
| 01 | SOURCE_CONTEXT | handoff and source priority | inventing data | docs | BESTAETIGT |
| 02 | REPO_CONTEXT | repo structure | deploy execution | root/archive | BESTAETIGT |
| 03 | GITHUB_LAYER | branch/write strategy | Cloudflare replacement | docs/GITHUB_CONTEXT.md | BESTAETIGT |
| 04 | CLOUDFLARE_LAYER | Worker deploy context | Discord Voice | worker/ | BESTAETIGT |
| 05 | DISCORD_LAYER | bot runtime | Worker API | discord-bot/ | BESTAETIGT |
| 06 | DISCORD_SECURITY_LAYER | permissions and safe replies | token values | docs/DISCORD_SECURITY_AUDIT.md | BESTAETIGT |
| 07 | BOT_COMMAND_LAYER | slash/button controls | Worker routes | discord-bot/src/discord | BESTAETIGT |
| 08 | RADIO_CORE_LAYER | voice relay | AutoDJ provider UI | discord-bot/src/voice | BESTAETIGT |
| 09 | AUTODJ_LAYER | SonicPanel adapter | voice relay | discord-bot/src/radio | OFFEN endpoints |
| 10 | STREAM_SOURCE_LAYER | presets/status sources | secret exposure | env examples | NACHZUTRAGEN |
| 11 | WORKER_LAYER | fetch handler | Discord Gateway | worker/src/index.js | BESTAETIGT |
| 12 | API_ROUTE_LAYER | public HTTP routes | admin bridge | worker/src/index.js | BESTAETIGT |
| 13 | WEBHOOK_LAYER | future posting | bot token handling | none | GEPLANT |
| 14 | REMOTE_CONTROL_LAYER | future protected bridge | public API | none | GEPLANT |
| 15 | DATA_STATE_LAYER | env/config state | database ownership | examples/wrangler | BESTAETIGT |
| 16 | SECURITY_SECRETS_LAYER | secret governance | secret values | docs/SECURITY_AND_SECRETS.md | BESTAETIGT |
| 17 | RUNTIME_LAYER | Node bot + Worker | mixing runtimes | discord-bot, worker | BESTAETIGT |
| 18 | DEPLOY_LAYER | deploy rules | blind pipeline edits | docs/DEPLOY_PROTECTION_RULES.md | BESTAETIGT |
| 19 | TEST_VALIDATION_LAYER | local checks | real secret testing | docs/TEST_PLAN.md | PASS |
| 20 | AUDIT_LAYER | audit runs | feature invention | docs/AUDIT_APPENDIX.md | PASS |
| 21 | CHANGELOG_ARCHIVE_LAYER | version/archive | deletion | CHANGELOG, archive | BESTAETIGT |
| 22 | OPEN_ITEMS_LAYER | missing data | guessing | docs/OPEN_QUESTIONS.md | OFFEN |
