"""666 RadioBotAI Visual Audit Cog — Phase 2C-22."""

from __future__ import annotations

import json
import discord
from discord.ext import commands

from radiobotai_audit_service import run_local_audit, format_audit_plain, visual_bar, write_audit_report


def audit_color(report):
    if report.get("ok"):
        return discord.Color.from_rgb(0, 255, 190)
    return discord.Color.from_rgb(255, 60, 120)


def make_visual_embed(report):
    embed = discord.Embed(
        title="666 RadioBotAI — Visual Audit",
        description=(
            f"**Status:** {'✅ PASS' if report.get('ok') else '❌ FAIL'}\n"
            f"**Upload:** `{report.get('upload_decision')}`\n"
            f"**Freeze:** `{report.get('freeze')}`"
        ),
        color=audit_color(report)
    )

    score_lines = []
    for key, value in report.get("scores", {}).items():
        score_lines.append(f"**{key}**\n{visual_bar(value)}")
    embed.add_field(name="🟦 Scores", value="\n".join(score_lines)[:1024], inline=False)

    check_lines = []
    for key, value in report.get("checks", {}).items():
        check_lines.append(f"{'✅' if value else '❌'} **{key}**")
    embed.add_field(name="🟩 Checks", value="\n".join(check_lines)[:1024], inline=False)

    protected_ok = sum(1 for v in report.get("protected_paths", {}).values() if v)
    protected_total = len(report.get("protected_paths", {}))
    route_ok = sum(1 for v in report.get("worker_routes", {}).values() if v)
    route_total = len(report.get("worker_routes", {}))
    embed.add_field(
        name="🛡️ Protection",
        value=f"Protected Paths: `{protected_ok}/{protected_total}`\nWorker Routes: `{route_ok}/{route_total}`",
        inline=True
    )
    embed.add_field(
        name="💾 Backup",
        value="External / NOT repo payload",
        inline=True
    )

    secret_hits = report.get("secret_hits") or []
    embed.add_field(
        name="🔐 Secrets",
        value="✅ Keine Treffer" if not secret_hits else "❌ Treffer:\n" + "\n".join(secret_hits[:5]),
        inline=False
    )
    embed.set_footer(text="666 RadioBotAI Audit / Repo-Safe Governance Split")
    return embed


class RadioBotAIAudit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="radioaudit", description="666 RadioBotAI Audit / Repo-Safe Governance Split")
    async def radioaudit(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply("Nutze /radioaudit visual, /radioaudit status, /radioaudit full oder /radioaudit write.")

    @radioaudit.command(name="visual", description="Farbiges optisches Audit anzeigen")
    async def radioaudit_visual(self, ctx):
        report = run_local_audit()
        await ctx.reply(embed=make_visual_embed(report))

    @radioaudit.command(name="status", description="Kurzer Audit-Status mit Balken")
    async def radioaudit_status(self, ctx):
        report = run_local_audit()
        text = format_audit_plain(report)
        if len(text) > 1900:
            text = text[:1900] + "…"
        await ctx.reply(f"```text\n{text}\n```")

    @radioaudit.command(name="full", description="Voller Audit-Bericht als JSON-Auszug")
    async def radioaudit_full(self, ctx):
        report = run_local_audit()
        text = json.dumps(report, indent=2, ensure_ascii=False)
        if len(text) > 1900:
            text = text[:1900] + "\n…"
        await ctx.reply(f"```json\n{text}\n```")

    @radioaudit.command(name="write", description="Audit-Bericht in Docs schreiben")
    async def radioaudit_write(self, ctx):
        path = write_audit_report()
        await ctx.reply(f"✅ Audit geschrieben: `{path}`")


async def setup(bot):
    await bot.add_cog(RadioBotAIAudit(bot))
