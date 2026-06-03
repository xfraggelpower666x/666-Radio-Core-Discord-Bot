# Master Handoff

Project: 666-Radio-Core-Discord-Bot
Owner: xfraggelpower666x
Branch: Codex
Version: v1.3.0
Status: PASS after Audit Run 03 with open production follow-ups

## Sources

1. 666RadioCoreDJ_v1_3_0.zip: BESTAETIGT active code source.
2. 666-Radio-Core-Discord-Bot_CODEX_MAXIMAL_HANDOFF_v1_1_0.md: BESTAETIGT documentation/audit contract.
3. Pasted v1.3.0 handoff: BESTAETIGT latest operational target.
4. Prior flat repo state: HISTORISCH, preserved in archive/previous-flat-radio-core-v1_0/.
5. 666RadioCoreDJ_Codex_Maximal_Handoff_Master_Prompt_v1_0_0.md: UNBEKANNT / NACHZUTRAGEN im aktuellen Arbeitsordner; user message from 2026-06-03 used as binding minimum contract.

## Active Architecture

- discord-bot/: Discord Gateway, Slash Commands, Button Panel, Voice Relay, SonicPanel/SHOUTcast adapters, ICY metadata reader, track-change detection, stream health monitor and optional Discord log-channel posting.
- worker/: Cloudflare Worker for /health, /nowplaying, /presets, /preset/1..5.
- docs/: Handoff, audit, deploy and security documentation.

## Non-Merge Rules

Discord Bot != Cloudflare Worker. Radio Core != AutoDJ. Public Worker API != private remote control. SonicPanel adapter != SHOUTcast fallback.

## Known Unknowns

SonicPanel Skip endpoint, SonicPanel Jingle endpoint, production Bot host, real stream URLs, Discord log channel ID and Cloudflare dashboard state are UNBEKANNT / NACHZUTRAGEN.
