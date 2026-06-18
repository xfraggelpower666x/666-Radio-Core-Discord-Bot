"""
666 RadioBotAI — SoundCloud Cog
Version: v1.2.3 / PHASE2C23

SoundCloud läuft über Lavalink mit scsearch:
"""

from __future__ import annotations

import logging
import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("radiobotai.soundcloud")


def build_soundcloud_query(query: str) -> str:
    q = (query or "").strip()
    if not q:
        raise ValueError("SoundCloud-Suchbegriff fehlt.")
    if q.lower().startswith("scsearch:"):
        return q
    return f"scsearch:{q}"


class RadioBotAISoundCloud(commands.Cog):
    """SoundCloud/Lavalink-Erweiterung für den 666 RadioBotAI."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _try_delegate_to_existing_play(self, interaction: discord.Interaction, search: str) -> bool:
        """
        Defensiver Anschluss an vorhandene Vocard-/Player-Logik.
        Wird später im Runtime-Test exakt an den vorhandenen Play-Hook gebunden.
        """
        candidate_names = (
            "play_query",
            "search_and_play",
            "vocard_play",
            "enqueue_query",
            "music_play",
        )

        for name in candidate_names:
            fn = getattr(self.bot, name, None)
            if callable(fn):
                try:
                    result = fn(interaction, search)
                    if hasattr(result, "__await__"):
                        await result
                    return True
                except Exception:
                    log.exception("SoundCloud delegation via bot.%s failed", name)
                    return False

        return False

    @app_commands.command(
        name="soundcloud",
        description="Sucht/queued einen Track über SoundCloud via Lavalink scsearch."
    )
    @app_commands.describe(query="SoundCloud Suchbegriff oder Trackname")
    async def soundcloud(self, interaction: discord.Interaction, query: str):
        search = build_soundcloud_query(query)
        await interaction.response.defer(thinking=True)

        delegated = await self._try_delegate_to_existing_play(interaction, search)
        if delegated:
            await interaction.followup.send(
                f"🟢 SoundCloud-Suche an Player übergeben:\n```text\n{search}\n```",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "🟡 SoundCloud Runtime ist vorbereitet, aber noch nicht an die konkrete Vocard-Play-Funktion dieses Forks gebunden.\n\n"
            "Nutze in der bestehenden Play-Suche diesen Lavalink-Query:\n"
            f"```text\n{search}\n```\n\n"
            "Nächster Integrationspunkt: vorhandene Vocard Play-/Queue-Funktion an `radiobotai_soundcloud.py` binden.",
            ephemeral=True,
        )

    @app_commands.command(
        name="scsearch",
        description="Alias für SoundCloud-Suche über Lavalink scsearch."
    )
    @app_commands.describe(query="SoundCloud Suchbegriff")
    async def scsearch(self, interaction: discord.Interaction, query: str):
        search = build_soundcloud_query(query)
        await interaction.response.defer(thinking=True)
        delegated = await self._try_delegate_to_existing_play(interaction, search)
        if delegated:
            await interaction.followup.send(f"🟢 scsearch übergeben:\n```text\n{search}\n```", ephemeral=True)
        else:
            await interaction.followup.send(f"🟡 scsearch vorbereitet:\n```text\n{search}\n```", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RadioBotAISoundCloud(bot))
