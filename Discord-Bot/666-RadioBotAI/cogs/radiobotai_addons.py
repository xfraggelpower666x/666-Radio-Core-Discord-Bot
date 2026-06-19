"""666 RadioBotAI Add-on Cog: AutoDJ / WebRadio / Worker-Bridge."""

import os
import aiohttp
from discord.ext import commands
from discord import app_commands

from radiobotai_permissions import require_dj, permission_status
from radiobotai_presets import get_presets, get_preset
from radiobotai_runtime_status import runtime_status


class RadioBotAIAddons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.worker_url = os.getenv("RADIOBOTAI_WORKER_URL", "https://666radiobotai.666soundsdesign-broadcaster.com").rstrip("/")
        self.admin_token = os.getenv("RADIOBOTAI_ADMIN_TOKEN", "")

    async def _post_worker(self, path: str, payload: dict):
        headers = {"content-type": "application/json"}
        if self.admin_token:
            headers["x-radiobotai-gate"] = self.admin_token
            headers["x-admin-token"] = self.admin_token
            headers["x-discord-gate-code"] = self.admin_token
            headers["authorization"] = f"Bearer {self.admin_token}"
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.worker_url}{path}", json=payload, headers=headers, timeout=15) as res:
                try:
                    data = await res.json()
                except Exception:
                    data = {"ok": False, "error": "invalid_json", "status": res.status}
                return res.status, data

    async def _get_worker(self, path: str):
        headers = {"accept": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.worker_url}{path}", headers=headers, timeout=15) as res:
                try:
                    data = await res.json()
                except Exception:
                    data = {"ok": False, "error": "invalid_json", "status": res.status}
                return res.status, data

    @commands.hybrid_group(name="radioaddon", description="666 RadioBotAI WebRadio Add-on Steuerung")
    async def radioaddon(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.reply("666 RadioBotAI Add-on: nutze /radioaddon status, /radioaddon skip, /radioaddon playlist oder /radioaddon shooter.")

    @radioaddon.command(name="status", description="666 RadioBotAI Status anzeigen")
    async def radio_status(self, ctx):
        data = runtime_status()
        perms = permission_status(ctx)
        await ctx.reply(
            "666 RadioBotAI Status OK"
            + f" | Uptime: {data.get('uptime_seconds')}s"
            + f" | DJ: {perms.get('current_user_dj')}"
            + f" | Admin: {perms.get('current_user_admin')}"
        )

    @radioaddon.command(name="nowplaying", description="NowPlaying vom Worker abrufen")
    async def radio_nowplaying(self, ctx):
        status, data = await self._get_worker("/nowplaying")
        title = data.get("title") or data.get("raw") or "unbekannt"
        await ctx.reply(f"666 RadioBotAI NowPlaying | HTTP {status} | {title}")

    @radioaddon.command(name="links", description="RadioBotAI Links anzeigen")
    async def radio_links(self, ctx):
        await ctx.reply(
            "666 RadioBotAI Links:\n"
            "Dashboard: https://666radiobotai.666soundsdesign-broadcaster.com/dashboard\n"
            "WebRadio: https://webradio.666soundsdesign-broadcaster.com\n"
            "TuneIn: https://tunein.com/radio/s357001"
        )

    @radioaddon.command(name="presets", description="Vorbereitete RadioBotAI Presets anzeigen")
    async def radio_presets(self, ctx):
        presets = get_presets()
        lines = [f"{key}: {value.get('label')}" for key, value in presets.items()]
        await ctx.reply("666 RadioBotAI Presets:\n" + "\n".join(lines))

    @radioaddon.command(name="presetinfo", description="Details zu einem RadioBotAI Preset anzeigen")
    @app_commands.describe(name="Preset-Name")
    async def radio_presetinfo(self, ctx, name: str):
        preset = get_preset(name)
        if not preset:
            await ctx.reply("Preset nicht gefunden.")
            return
        await ctx.reply(f"{name}: {preset.get('label')} — {preset.get('description')}")

    @radioaddon.command(name="skip", description="AutoDJ aktuelles Lied überspringen")
    async def radio_skip(self, ctx):
        if not await require_dj(ctx):
            return
        status, data = await self._post_worker("/radio/autodj/skip", {})
        ok = data.get("ok") is not False and status < 400
        await ctx.reply(("AutoDJ Skip OK" if ok else "AutoDJ Skip NICHT OK") + f" | HTTP {status}")

    @radioaddon.command(name="playlist", description="AutoDJ Playlist während On Air wechseln")
    @app_commands.describe(playlist="Playlist-ID oder Playlist-Name")
    async def radio_playlist(self, ctx, playlist: str):
        if not await require_dj(ctx):
            return
        status, data = await self._post_worker("/radio/autodj/playlist", {"playlist": playlist})
        ok = data.get("ok") is not False and status < 400
        await ctx.reply(("Playlistwechsel OK" if ok else "Playlistwechsel NICHT OK") + f" | HTTP {status}")

    @radioaddon.command(name="shooter", description="Nachricht über Discord-Shooter senden")
    @app_commands.describe(message="Nachricht", target="main, secondary, url3 oder all")
    async def radio_shooter(self, ctx, message: str, target: str = "main"):
        if not await require_dj(ctx):
            return
        status, data = await self._post_worker("/api/discord/message", {"message": message, "target": target})
        ok = data.get("ok") is not False and status < 400
        await ctx.reply(("Discord Shooter OK" if ok else "Discord Shooter NICHT OK") + f" | HTTP {status}")


async def setup(bot):
    await bot.add_cog(RadioBotAIAddons(bot))
