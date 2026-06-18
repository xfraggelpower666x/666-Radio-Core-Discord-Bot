"""666 RadioBotAI AI Cog — Phase 2C-6."""

from discord.ext import commands
from discord import app_commands

from radiobotai_ai_client import RadioBotAIAIClient, ai_status_config
from radiobotai_permissions import require_dj


class RadioBotAIAI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = RadioBotAIAIClient()

    @commands.hybrid_group(name="radioai", description="666 RadioBotAI AI Add-on")
    async def radioai(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply("666 RadioBotAI AI: nutze /radioai ask oder /radioai status.")

    @radioai.command(name="status", description="AI Add-on Status anzeigen")
    async def radioai_status(self, ctx):
        cfg = ai_status_config()
        await ctx.reply(
            "666 RadioBotAI AI Status"
            + f" | Worker: {cfg.get('worker_url')}"
            + f" | Admin Token configured: {cfg.get('admin_token_configured')}"
        )

    @radioai.command(name="ask", description="AI Add-on über den RadioBotAI Worker fragen")
    @app_commands.describe(prompt="Frage / Aufgabe für das AI-Addon")
    async def radioai_ask(self, ctx, prompt: str):
        if not await require_dj(ctx):
            return
        status, data = await self.client.ask(prompt)
        ok = status < 400 and data.get("ok") is not False
        answer = data.get("answer") or data.get("message") or data.get("error") or "keine Antwort"
        if len(answer) > 1800:
            answer = answer[:1800] + "…"
        await ctx.reply(("AI OK" if ok else "AI NICHT OK") + f" | HTTP {status}\n{answer}")


async def setup(bot):
    await bot.add_cog(RadioBotAIAI(bot))
