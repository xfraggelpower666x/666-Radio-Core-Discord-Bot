"""666 RadioBotAI radio control layer.

Diese Datei erweitert die vorhandene Vocard/Voicelink-Playback-Engine gezielt
für den 666SOUNDsDESIGn WebRadio-Betrieb. Die Musikbot-Architektur bleibt
intakt; Radio-Funktionen werden als eigene Slash-/Hybrid-Command-Gruppe ergänzt.
"""

from __future__ import annotations

import discord
import voicelink

from discord import app_commands
from discord.ext import commands
from typing import Optional

from voicelink import Config, MongoDBHandler
from voicelink.utils import dispatch_message


BOT_INFO_TEXT = """
BOT NAME:
666 RadioBotAI

BOT-TYP:
Discord Voice Radio Bot / WebRadio Stream Player

PROJEKT:
666SOUNDsDESIGn WebRadio
Discord Radio Stream Playback Bot

KURZBESCHREIBUNG:
666 RadioBotAI ist der Discord-Bot für den 666SOUNDsDESIGn WebRadio-Stream.
Der Bot verbindet sich mit einem Discord-Voice-Channel und spielt den laufenden
WebRadio-Stream ab. Er dient nicht als Chatbot, sondern als Radio-Playback- und
Stream-Control-Bot.

HAUPTAUFGABE:
Der Bot soll den WebRadio-Stream zuverlässig im Discord-Voice-Channel wiedergeben
und einfache Steuerbefehle für Wiedergabe, Lautstärke, Streamstatus und aktuelle
Titelinformationen bereitstellen.

FUNKTIONEN:
- WebRadio-Stream im Discord Voice Channel abspielen
- Bot mit Voice Channel verbinden
- Stream starten und stoppen
- Wiedergabe pausieren und fortsetzen
- Lautstärke steuern
- aktuellen Streamstatus anzeigen
- Now Playing anzeigen, sofern Metadaten verfügbar sind
- Verbindung prüfen und Stream neu starten
- Admin-Rolle für Radio-Steuerung setzen oder erstellen
""".strip()


class Radio(commands.Cog):
    """RadioBotAI Commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _defer(self, ctx: commands.Context, *, ephemeral: bool = False) -> None:
        try:
            if ctx.interaction and not ctx.interaction.response.is_done():
                await ctx.defer(ephemeral=ephemeral)
        except Exception:
            pass

    async def _reply(self, ctx: commands.Context, content: str = None, *, embed: discord.Embed = None, ephemeral: bool = False):
        return await dispatch_message(ctx, embed or content, ephemeral=ephemeral)

    async def _get_settings(self, guild_id: int) -> dict:
        return await MongoDBHandler.get_settings(guild_id)

    async def _update_settings(self, guild_id: int, data: dict) -> None:
        await MongoDBHandler.update_settings(guild_id, {"$set": data}, upsert=True)

    def _configured_admin_role_ids(self, settings: dict) -> set[int]:
        role_ids = set(Config().radio.get("allowed_role_ids", []))
        role_id = int(settings.get("radio_admin_role_id") or Config().radio.get("admin_role_id") or 0)
        if role_id:
            role_ids.add(role_id)
        return role_ids

    def _is_radio_admin(self, member: discord.Member, settings: dict) -> bool:
        if member.id in Config().bot_access_user:
            return True
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
            return True
        role_ids = self._configured_admin_role_ids(settings)
        return any(role.id in role_ids for role in member.roles)

    async def _require_admin(self, ctx: commands.Context, settings: dict) -> bool:
        if self._is_radio_admin(ctx.author, settings):
            return True
        await self._reply(ctx, "Keine RadioBotAI-Adminberechtigung. Erlaubt sind Server-Admin, Server verwalten oder die konfigurierte Radio-Admin-Rolle.", ephemeral=True)
        return False

    def _embed(self, title: str, description: str = None) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=Config().embed_color,
        )
        embed.set_footer(text="666 RadioBotAI • 666SOUNDsDESIGn WebRadio")
        return embed

    def _clean_stream_url_for_display(self, url: str) -> str:
        if not url:
            return "nicht gesetzt"
        # Stream-URLs sind normalerweise öffentlich; Query-Parameter werden trotzdem nicht voll angezeigt.
        return url.split("?")[0]

    async def _log(self, guild: discord.Guild, text: str) -> None:
        try:
            settings = await self._get_settings(guild.id)
            channel_id = int(settings.get("radio_log_text_channel_id") or Config().radio.get("log_text_channel_id") or 0)
            channel = guild.get_channel(channel_id) if channel_id else None
            if channel:
                await channel.send(text, allowed_mentions=discord.AllowedMentions.none())
        except Exception:
            pass

    async def _get_stream_url(self, guild_id: int) -> str:
        settings = await self._get_settings(guild_id)
        return settings.get("radio_stream_url") or Config().radio.get("stream_url") or ""

    async def _resolve_voice_channel(self, ctx: commands.Context, channel: Optional[discord.VoiceChannel] = None) -> Optional[discord.VoiceChannel]:
        if channel:
            return channel
        settings = await self._get_settings(ctx.guild.id)
        channel_id = int(settings.get("radio_voice_channel_id") or Config().radio.get("default_voice_channel_id") or 0)
        if channel_id:
            found = ctx.guild.get_channel(channel_id)
            if isinstance(found, discord.VoiceChannel):
                return found
        if ctx.author.voice and isinstance(ctx.author.voice.channel, discord.VoiceChannel):
            return ctx.author.voice.channel
        return None

    async def _get_or_connect_player(self, ctx: commands.Context, channel: discord.VoiceChannel) -> voicelink.Player:
        player: voicelink.Player = ctx.guild.voice_client
        if player and player.channel and player.channel.id != channel.id:
            await player.teardown()
            player = None
        if not player:
            player = await voicelink.connect_channel(ctx, channel)
        return player

    async def _start_stream(self, ctx: commands.Context, stream_url: str, channel: discord.VoiceChannel, *, reset: bool = True) -> voicelink.Player:
        player = await self._get_or_connect_player(ctx, channel)

        if reset:
            try:
                await player.stop()
            except Exception:
                pass
            player.queue._queue.clear()
            player.queue._position = 0

        tracks = await player.get_tracks(stream_url, requester=ctx.author)
        if not tracks:
            raise voicelink.VoicelinkException("Stream konnte nicht geladen werden. Prüfe RADIO_STREAM_URL oder Lavalink-Quellen/Netzwerk.")

        track = tracks.tracks[0] if isinstance(tracks, voicelink.Playlist) else tracks[0]
        await player.add_track(track, duplicate=False)
        volume = max(0, min(int(Config().radio.get("default_volume", 100)), 200))
        await player.set_volume(volume, ctx.author)
        if not player.is_playing:
            await player.do_next()
        return player

    @commands.hybrid_group(name="radio", aliases=["r"], invoke_without_command=True)
    async def radio(self, ctx: commands.Context) -> None:
        """Zeigt den aktuellen RadioBotAI-Status."""
        await self.radio_status(ctx)

    @radio.command(name="play", aliases=["start"])
    @app_commands.describe(
        stream_url="Optional: anderer Stream-Link für diesen Start.",
        channel="Optional: Voice-Channel, in den der Bot verbinden soll."
    )
    async def radio_play(self, ctx: commands.Context, stream_url: Optional[str] = None, channel: Optional[discord.VoiceChannel] = None) -> None:
        """Startet den WebRadio-Stream."""
        await self._defer(ctx)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return

        stream_url = stream_url or settings.get("radio_stream_url") or Config().radio.get("stream_url")
        if not stream_url:
            return await self._reply(ctx, "RADIO_STREAM_URL ist noch nicht gesetzt. Nutze `/radio setstream <url>` oder trage RADIO_STREAM_URL in `.env` ein.", ephemeral=True)

        channel = await self._resolve_voice_channel(ctx, channel)
        if not channel:
            return await self._reply(ctx, "Kein Voice-Channel gefunden. Geh in einen Voice-Channel oder setze `/radio setvoice`.", ephemeral=True)

        try:
            player = await self._start_stream(ctx, stream_url, channel)
        except Exception as exc:
            return await self._reply(ctx, f"RadioBotAI konnte den Stream nicht starten: `{exc}`", ephemeral=True)

        embed = self._embed("666 RadioBotAI läuft", f"Voice: {channel.mention}\nStream: `{self._clean_stream_url_for_display(stream_url)}`\nVolume: `{player.volume}%`")
        await self._reply(ctx, embed=embed)
        await self._log(ctx.guild, f"📻 666 RadioBotAI gestartet in {channel.name} von {ctx.author}.")

    @radio.command(name="stop", aliases=["leave"])
    async def radio_stop(self, ctx: commands.Context) -> None:
        """Stoppt den Stream und trennt den Bot vom Voice-Channel."""
        await self._defer(ctx)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        player: voicelink.Player = ctx.guild.voice_client
        if not player:
            return await self._reply(ctx, "RadioBotAI ist aktuell mit keinem Voice-Channel verbunden.", ephemeral=True)
        await player.teardown()
        await self._reply(ctx, "RadioBotAI wurde gestoppt und getrennt.")
        await self._log(ctx.guild, f"⏹️ 666 RadioBotAI gestoppt von {ctx.author}.")

    @radio.command(name="pause")
    async def radio_pause(self, ctx: commands.Context) -> None:
        """Pausiert die Wiedergabe."""
        await self._defer(ctx)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        player: voicelink.Player = ctx.guild.voice_client
        if not player or not player.current:
            return await self._reply(ctx, "Es läuft aktuell kein Radio-Stream.", ephemeral=True)
        await player.set_pause(True, ctx.author)
        await self._reply(ctx, "RadioBotAI pausiert.")

    @radio.command(name="resume")
    async def radio_resume(self, ctx: commands.Context) -> None:
        """Setzt die Wiedergabe fort."""
        await self._defer(ctx)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        player: voicelink.Player = ctx.guild.voice_client
        if not player or not player.current:
            return await self._reply(ctx, "Es läuft aktuell kein Radio-Stream.", ephemeral=True)
        await player.set_pause(False, ctx.author)
        await self._reply(ctx, "RadioBotAI läuft weiter.")

    @radio.command(name="repair", aliases=["restart", "reload"])
    async def radio_repair(self, ctx: commands.Context) -> None:
        """Repariert die Wiedergabe durch sauberes Neuverbinden und erneutes Laden des Streams."""
        await self._defer(ctx)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        stream_url = settings.get("radio_stream_url") or Config().radio.get("stream_url")
        if not stream_url:
            return await self._reply(ctx, "Kein Stream gesetzt. Nutze `/radio setstream <url>`.", ephemeral=True)
        channel = await self._resolve_voice_channel(ctx)
        if not channel:
            return await self._reply(ctx, "Kein Voice-Channel gefunden. Geh in einen Voice-Channel oder setze `/radio setvoice`.", ephemeral=True)
        player: voicelink.Player = ctx.guild.voice_client
        if player:
            try:
                await player.teardown()
            except Exception:
                pass
        try:
            player = await self._start_stream(ctx, stream_url, channel, reset=True)
        except Exception as exc:
            return await self._reply(ctx, f"Repair fehlgeschlagen: `{exc}`", ephemeral=True)
        await self._reply(ctx, f"RadioBotAI Repair abgeschlossen. Stream läuft in {channel.mention} mit `{player.volume}%`.")
        await self._log(ctx.guild, f"🛠️ 666 RadioBotAI Repair ausgeführt von {ctx.author}.")

    @radio.command(name="volume")
    @app_commands.describe(value="Lautstärke 0-200. Standard: 100. Safe: 0-150. Boost: 151-200.")
    async def radio_volume(self, ctx: commands.Context, value: app_commands.Range[int, 0, 200]) -> None:
        """Setzt die Stream-Lautstärke."""
        await self._defer(ctx)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        player: voicelink.Player = ctx.guild.voice_client
        if not player:
            return await self._reply(ctx, "RadioBotAI ist aktuell nicht verbunden.", ephemeral=True)
        await player.set_volume(int(value), ctx.author)
        await self._reply(ctx, f"RadioBotAI Volume gesetzt: `{value}%`.")

    @radio.command(name="nowplaying", aliases=["np"])
    async def radio_nowplaying(self, ctx: commands.Context) -> None:
        """Zeigt den aktuell geladenen Stream/Track."""
        await self._defer(ctx, ephemeral=True)
        player: voicelink.Player = ctx.guild.voice_client
        if not player or not player.current:
            return await self._reply(ctx, "Aktuell läuft kein Radio-Stream.", ephemeral=True)
        track = player.current
        embed = self._embed("Now Playing", f"Titel: **{track.title}**\nQuelle: `{track.source.title()}`\nLive: `{track.is_stream}`\nVolume: `{player.volume}%`")
        if track.uri:
            embed.add_field(name="Stream", value=f"`{self._clean_stream_url_for_display(track.uri)}`", inline=False)
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        await self._reply(ctx, embed=embed, ephemeral=True)

    @radio.command(name="status")
    async def radio_status(self, ctx: commands.Context) -> None:
        """Zeigt Verbindungsstatus, Stream-URL und Admin-Rolle."""
        await self._defer(ctx, ephemeral=True)
        settings = await self._get_settings(ctx.guild.id)
        stream_url = settings.get("radio_stream_url") or Config().radio.get("stream_url") or ""
        voice_id = int(settings.get("radio_voice_channel_id") or Config().radio.get("default_voice_channel_id") or 0)
        voice_channel = ctx.guild.get_channel(voice_id) if voice_id else None
        player: voicelink.Player = ctx.guild.voice_client
        admin_role_id = int(settings.get("radio_admin_role_id") or Config().radio.get("admin_role_id") or 0)
        admin_role = ctx.guild.get_role(admin_role_id) if admin_role_id else None

        embed = self._embed("666 RadioBotAI Status")
        embed.add_field(name="Verbindung", value=(f"verbunden mit {player.channel.mention}" if player and player.channel else "nicht verbunden"), inline=False)
        embed.add_field(name="Playback", value=("läuft" if player and player.current and not player.is_paused else "pausiert" if player and player.current else "kein Stream"), inline=True)
        embed.add_field(name="Volume", value=(f"{player.volume}%" if player else "-"), inline=True)
        embed.add_field(name="Standard Voice", value=(voice_channel.mention if voice_channel else "nicht gesetzt"), inline=False)
        embed.add_field(name="Stream", value=f"`{self._clean_stream_url_for_display(stream_url)}`", inline=False)
        embed.add_field(name="Admin-Rolle", value=(admin_role.mention if admin_role else Config().radio.get("admin_role_name", "666 RadioBotAI Admin")), inline=False)
        await self._reply(ctx, embed=embed, ephemeral=True)

    @radio.command(name="info")
    async def radio_info(self, ctx: commands.Context) -> None:
        """Zeigt die RadioBotAI-Projektinformation."""
        embed = self._embed("666 RadioBotAI Info", BOT_INFO_TEXT[:4000])
        await self._reply(ctx, embed=embed, ephemeral=True)

    @radio.command(name="setstream")
    @app_commands.describe(stream_url="Direkter WebRadio-Stream-Link, z. B. https://.../stream")
    async def radio_setstream(self, ctx: commands.Context, stream_url: str) -> None:
        """Speichert die Stream-URL für diesen Discord-Server."""
        await self._defer(ctx, ephemeral=True)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        if not stream_url.startswith(("http://", "https://")):
            return await self._reply(ctx, "Ungültige Stream-URL. Erlaubt sind http:// oder https://.", ephemeral=True)
        await self._update_settings(ctx.guild.id, {"radio_stream_url": stream_url})
        await self._reply(ctx, f"Stream-URL gespeichert: `{self._clean_stream_url_for_display(stream_url)}`", ephemeral=True)

    @radio.command(name="setvoice")
    @app_commands.describe(channel="Voice-Channel, in dem RadioBotAI standardmäßig laufen soll.")
    async def radio_setvoice(self, ctx: commands.Context, channel: discord.VoiceChannel) -> None:
        """Speichert den Standard-Voice-Channel."""
        await self._defer(ctx, ephemeral=True)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        await self._update_settings(ctx.guild.id, {"radio_voice_channel_id": channel.id})
        await self._reply(ctx, f"Standard-Voice-Channel gespeichert: {channel.mention}", ephemeral=True)

    @radio.command(name="setlog")
    @app_commands.describe(channel="Text-Channel für RadioBotAI Logs.")
    async def radio_setlog(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        """Speichert den Log-/Status-Textchannel."""
        await self._defer(ctx, ephemeral=True)
        settings = await self._get_settings(ctx.guild.id)
        if not await self._require_admin(ctx, settings):
            return
        await self._update_settings(ctx.guild.id, {"radio_log_text_channel_id": channel.id})
        await self._reply(ctx, f"Radio-Log-Channel gespeichert: {channel.mention}", ephemeral=True)

    @radio.command(name="setadminrole")
    @app_commands.describe(role="Rolle, die RadioBotAI steuern darf.")
    async def radio_setadminrole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Setzt eine vorhandene RadioBotAI-Adminrolle."""
        await self._defer(ctx, ephemeral=True)
        settings = await self._get_settings(ctx.guild.id)
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            return await self._reply(ctx, "Nur Server-Admins oder Mitglieder mit `Server verwalten` dürfen die Radio-Adminrolle setzen.", ephemeral=True)
        await self._update_settings(ctx.guild.id, {"radio_admin_role_id": role.id})
        await self._reply(ctx, f"RadioBotAI-Adminrolle gespeichert: {role.mention}", ephemeral=True)

    @radio.command(name="setupadmin")
    @app_commands.describe(
        member="Optional: Mitglied, dem die Rolle direkt gegeben wird.",
        administrator="Wenn aktiv, erstellt die Rolle mit Discord-Administratorrecht. Standard ist sicherer Radio-Admin ohne Volladmin."
    )
    async def radio_setupadmin(self, ctx: commands.Context, member: Optional[discord.Member] = None, administrator: bool = False) -> None:
        """Erstellt/registriert die RadioBotAI-Adminrolle und weist sie optional zu."""
        await self._defer(ctx, ephemeral=True)
        if not (ctx.author.guild_permissions.administrator or ctx.author.guild_permissions.manage_guild):
            return await self._reply(ctx, "Nur Server-Admins oder Mitglieder mit `Server verwalten` dürfen die RadioBotAI-Adminrolle einrichten.", ephemeral=True)

        role_name = Config().radio.get("admin_role_name", "666 RadioBotAI Admin")
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        created = False

        if not role:
            if not ctx.guild.me.guild_permissions.manage_roles:
                return await self._reply(ctx, "Mir fehlt `Rollen verwalten`. Lade den Bot mit passenden Berechtigungen neu ein oder gib meiner Bot-Rolle `Rollen verwalten`.", ephemeral=True)
            perms = discord.Permissions(administrator=True) if administrator else discord.Permissions.none()
            role = await ctx.guild.create_role(
                name=role_name,
                permissions=perms,
                reason="666 RadioBotAI Adminrolle eingerichtet"
            )
            created = True

        target = member or ctx.author
        assigned = False
        if ctx.guild.me.guild_permissions.manage_roles and role < ctx.guild.me.top_role and role not in target.roles:
            await target.add_roles(role, reason="666 RadioBotAI Adminrolle zugewiesen")
            assigned = True

        await self._update_settings(ctx.guild.id, {"radio_admin_role_id": role.id})
        embed = self._embed("RadioBotAI Adminrolle eingerichtet")
        embed.add_field(name="Rolle", value=role.mention, inline=False)
        embed.add_field(name="Neu erstellt", value="ja" if created else "nein", inline=True)
        embed.add_field(name="Zugewiesen", value=(target.mention if assigned else "nicht automatisch zugewiesen"), inline=True)
        embed.add_field(name="Discord-Administratorrecht", value="ja" if administrator else "nein", inline=True)
        await self._reply(ctx, embed=embed, ephemeral=True)

    @radio.command(name="invite")
    async def radio_invite(self, ctx: commands.Context) -> None:
        """Erzeugt Invite-Links mit passenden Botberechtigungen."""
        client_id = Config().client_id or self.bot.user.id
        radio_perms = discord.Permissions(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            read_message_history=True,
            connect=True,
            speak=True,
            use_voice_activation=True,
            manage_messages=True,
            manage_roles=True,
            move_members=True,
        )
        admin_perms = discord.Permissions(administrator=True)
        radio_url = discord.utils.oauth_url(client_id, permissions=radio_perms, scopes=("bot", "applications.commands"))
        admin_url = discord.utils.oauth_url(client_id, permissions=admin_perms, scopes=("bot", "applications.commands"))
        embed = self._embed("RadioBotAI Invite")
        embed.add_field(name="Empfohlen", value=f"[Bot mit Radio-Rechten einladen]({radio_url})", inline=False)
        embed.add_field(name="Volladmin", value=f"[Bot mit Administratorrecht einladen]({admin_url})", inline=False)
        await self._reply(ctx, embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Radio(bot))
