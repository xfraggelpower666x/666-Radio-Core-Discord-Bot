"""
Discord-Bot/666-RadioBotAI/cogs/radiobotai_djpanel.py
======================================================
DJ Panel Integration Cog -- 666SOUNDsDESIGn WebRadio
Slash-Commands: /voteskip  /skip  /nowplaying  /listeners

DJ Panel URL aus MongoDB-Einstellung "radio_djpanel_url" oder Env DJPANEL_URL.
Kein Eingriff in Vocard/Voicelink-Kern, Lavalink oder Audio-Logik.
"""

from __future__ import annotations

import os
import re
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from voicelink import Config, MongoDBHandler
from voicelink.utils import dispatch_message


COG_VERSION = "1.0.0"

ENDPOINTS = {
    "votes":      "/skip/votes",
    "vote":       "/skip/vote",
    "skip":       "/skip",
    "nowplaying": "/api/nowplaying",
}

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=8)


def _embed(title: str, description: str = None, *, color: int = 0x16fff3) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"666 RadioBotAI · DJ Panel v{COG_VERSION}")
    return embed


class DJPanel(commands.Cog, name="DJ Panel"):
    """Verbindet den Bot mit dem 666SOUNDsDESIGn DJ Control Panel."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._session: Optional[aiohttp.ClientSession] = None

    async def cog_load(self) -> None:
        self._session = aiohttp.ClientSession(timeout=REQUEST_TIMEOUT)

    async def cog_unload(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # -- helpers -----------------------------------------------------------

    async def _defer(self, ctx: commands.Context, *, ephemeral: bool = False) -> None:
        try:
            if ctx.interaction and not ctx.interaction.response.is_done():
                await ctx.defer(ephemeral=ephemeral)
        except Exception:
            pass

    async def _reply(self, ctx, content=None, *, embed=None, ephemeral=False):
        return await dispatch_message(ctx, embed or content, ephemeral=ephemeral)

    async def _settings(self, guild_id: int) -> dict:
        return await MongoDBHandler.get_settings(guild_id)

    def _is_admin(self, member: discord.Member, settings: dict) -> bool:
        if member.id in Config().bot_access_user:
            return True
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
        role_ids = set(Config().radio.get("allowed_role_ids", []))
        role_id = int(settings.get("radio_admin_role_id") or Config().radio.get("admin_role_id") or 0)
        if role_id:
            role_ids.add(role_id)
        return any(r.id in role_ids for r in member.roles)

    async def _require_admin(self, ctx, settings) -> bool:
        if self._is_admin(ctx.author, settings):
            return True
        await self._reply(ctx, "Keine RadioBotAI-Admin-Berechtigung.", ephemeral=True)
        return False

    async def _panel_url(self, guild_id: int) -> Optional[str]:
        s = await self._settings(guild_id)
        url = s.get("radio_djpanel_url") or os.environ.get("DJPANEL_URL") or ""
        return url.rstrip("/") if url else None

    async def _get(self, base: str, ep: str) -> dict:
        async with self._session.get(base + ep) as r:
            r.raise_for_status()
            return await r.json(content_type=None)

    async def _post(self, base: str, ep: str, payload: dict = None) -> dict:
        async with self._session.post(base + ep, json=payload or {}) as r:
            r.raise_for_status()
            return await r.json(content_type=None)

    def _no_panel_embed(self):
        return _embed(
            "⚙️ DJ Panel nicht konfiguriert",
            "Die DJ Panel URL ist nicht gesetzt.\n"
            "Ein Admin kann sie als Umgebungsvariable `DJPANEL_URL` setzen.",
            color=0xff3dbb,
        )

    # -- /voteskip ---------------------------------------------------------

    @commands.hybrid_command(name="voteskip", description="Stimme ab, den aktuellen Song zu skippen.")
    @app_commands.guild_only()
    async def voteskip(self, ctx: commands.Context) -> None:
        """Gibt eine Vote-Skip-Stimme ab. Wenn genug Stimmen: automatischer Skip."""
        await self._defer(ctx, ephemeral=True)

        base = await self._panel_url(ctx.guild.id)
        if not base:
            return await self._reply(ctx, embed=self._no_panel_embed(), ephemeral=True)

        try:
            status = await self._get(base, ENDPOINTS["votes"])
        except Exception as exc:
            return await self._reply(ctx, embed=_embed("❌ DJ Panel nicht erreichbar", str(exc), color=0xff3d68), ephemeral=True)

        votes_now  = int(status.get("votes",   0))
        votes_need = int(status.get("required", 3))
        skipped    = bool(status.get("skipped",   False))
        user_voted = bool(status.get("userVoted", False))

        if skipped:
            return await self._reply(ctx, embed=_embed("⏭️ Bereits geskippt", "Der Song wurde gerade geskippt!"), ephemeral=True)

        if user_voted:
            return await self._reply(ctx,
                embed=_embed("✋ Du hast bereits abgestimmt",
                             f"Aktuell: **{votes_now} / {votes_need}** Stimmen.", color=0xffaa26),
                ephemeral=True)

        try:
            result = await self._post(base, ENDPOINTS["vote"], {
                "userId":   str(ctx.author.id),
                "userName": str(ctx.author.display_name),
                "source":   "discord",
            })
        except Exception as exc:
            return await self._reply(ctx, embed=_embed("❌ Vote fehlgeschlagen", str(exc), color=0xff3d68), ephemeral=True)

        new_votes  = int(result.get("votes",    votes_now + 1))
        new_need   = int(result.get("required", votes_need))
        skipped_now= bool(result.get("skipped", False))

        if skipped_now:
            pub = _embed(
                "⏭️ Song wird geskippt!",
                f"{ctx.author.mention} gab die letzte Stimme ({new_votes}/{new_need}) — nächster Track!",
            )
            await dispatch_message(ctx, pub)
            return await self._reply(ctx, embed=_embed("⏭️ Geskippt!", f"{new_votes}/{new_need} Stimmen — done!"), ephemeral=True)

        remaining = new_need - new_votes
        await self._reply(ctx,
            embed=_embed(
                "✅ Stimme gezählt",
                f"**{new_votes} / {new_need}** Stimmen — noch **{remaining}** benötigt.",
            ),
            ephemeral=True,
        )

    # -- /skip (admin) -----------------------------------------------------

    @commands.hybrid_command(name="skip", description="[Admin] Überspringt den Song sofort.")
    @app_commands.guild_only()
    async def skip(self, ctx: commands.Context) -> None:
        """Admin-Befehl: Sofortiger Skip ohne Abstimmung."""
        await self._defer(ctx, ephemeral=True)

        settings = await self._settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return

        base = await self._panel_url(ctx.guild.id)
        if not base:
            return await self._reply(ctx, embed=self._no_panel_embed(), ephemeral=True)

        try:
            result = await self._post(base, ENDPOINTS["skip"], {
                "source":   "discord-admin",
                "userId":   str(ctx.author.id),
                "userName": str(ctx.author.display_name),
            })
        except Exception as exc:
            return await self._reply(ctx, embed=_embed("❌ Skip fehlgeschlagen", str(exc), color=0xff3d68), ephemeral=True)

        ok = result.get("ok", True)
        if ok:
            await dispatch_message(ctx, _embed(
                "⏭️ Admin-Skip",
                f"{ctx.author.mention} hat den Song übersprungen.",
                color=0xff3dbb,
            ))
        await self._reply(ctx,
            embed=_embed("⏭️ Song geskippt" if ok else "⚠️ Unbekannte Antwort",
                         "Ausgeführt." if ok else str(result)),
            ephemeral=True,
        )

    # -- /nowplaying -------------------------------------------------------

    @commands.hybrid_command(name="nowplaying", description="Zeigt den aktuell laufenden Song.")
    @app_commands.guild_only()
    async def nowplaying_cmd(self, ctx: commands.Context) -> None:
        """Aktueller Song aus dem DJ Panel / Stream-Metadata."""
        await self._defer(ctx)

        base = await self._panel_url(ctx.guild.id)
        if not base:
            return await self._reply(ctx, embed=self._no_panel_embed(), ephemeral=True)

        try:
            meta = await self._get(base, ENDPOINTS["nowplaying"])
        except Exception as exc:
            return await self._reply(ctx, embed=_embed("❌ Fehler", str(exc), color=0xff3d68), ephemeral=True)

        title     = (meta.get("title") or meta.get("songtitle") or "Unbekannt").strip()
        listeners = str(meta.get("listeners") or meta.get("currentlisteners") or "–")
        uniq      = str(meta.get("uniq") or "–")
        bitrate   = str(meta.get("bitrate") or "–")
        dj        = (meta.get("dj") or "").strip()
        art       = meta.get("art_full") or meta.get("art") or ""
        if re.match(r"no.?dj|autodj|auto-dj", dj, re.I):
            dj = ""

        embed = _embed("U0001f3b5 Now Playing — 666SOUNDsDESIGn")
        embed.add_field(name="Track",    value=f"**{title}**",                          inline=False)
        if dj:
            embed.add_field(name="U0001f534 Live DJ", value=dj,                        inline=True)
        embed.add_field(name="U0001f465 Listener",    value=listeners,                 inline=True)
        embed.add_field(name="✨ Unique",          value=uniq,                      inline=True)
        embed.add_field(name="U0001f4fb Bitrate",     value=f"{bitrate} kbps" if bitrate != "–" else "–", inline=True)
        if art:
            embed.set_thumbnail(url=art)
        await self._reply(ctx, embed=embed)

    # -- /listeners --------------------------------------------------------

    @commands.hybrid_command(name="listeners", description="Zeigt die aktuelle Hörer-Anzahl.")
    @app_commands.guild_only()
    async def listeners_cmd(self, ctx: commands.Context) -> None:
        """Hörer- und Unique-Listener-Anzahl aus dem Stream."""
        await self._defer(ctx)

        base = await self._panel_url(ctx.guild.id)
        if not base:
            return await self._reply(ctx, embed=self._no_panel_embed(), ephemeral=True)

        try:
            meta = await self._get(base, ENDPOINTS["nowplaying"])
        except Exception as exc:
            return await self._reply(ctx, embed=_embed("❌ Fehler", str(exc), color=0xff3d68), ephemeral=True)

        listeners = str(meta.get("listeners") or meta.get("currentlisteners") or "–")
        uniq      = str(meta.get("uniq") or "–")
        await self._reply(ctx, embed=_embed(
            "U0001f465 Listener — 666SOUNDsDESIGn WebRadio",
            f"**Online:** {listeners}\n**Unique:** {uniq}",
        ))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DJPanel(bot))