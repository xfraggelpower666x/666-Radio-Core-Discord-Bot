from __future__ import annotations

import discord
from discord import app_commands

from radio_actions import RadioAction


def setup_commands(tree: app_commands.CommandTree, radio) -> None:
    """Registriert die konfliktfreien Slash-Commands der lokalen AutoDJ-Engine."""
    db = radio.db

    @tree.command(name="track", description="Sucht einen lokalen Titel und spielt ihn über den AutoDJ")
    @app_commands.describe(query="Interpret, Titel, Datenbank-ID oder unterstützter Weblink")
    async def track(interaction: discord.Interaction, query: str):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("❌ Dieser Befehl funktioniert nur auf einem Discord-Server.", ephemeral=True)
            return
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Du musst in einem Voice-Channel sein.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        if getattr(radio, "ensure_local_mode", None):
            await radio.ensure_local_mode(interaction.guild, interaction.user.voice.channel)

        query_strip = query.strip()
        if query_strip.startswith(("http://", "https://")):
            if radio.voice_channel_id is None:
                radio.dispatch(RadioAction.JOIN, interaction.user.voice.channel.id, user=interaction.user)
            radio.dispatch(RadioAction.ADD_EXT_LINK, query_strip, user=interaction.user)
            await interaction.followup.send("✅ Weblink wurde der AutoDJ-Queue hinzugefügt.", ephemeral=True)
            return

        song = await db.get_song_by_id(int(query_strip)) if query_strip.isdigit() else None
        if not song:
            song = await db.get_song_by_path(query_strip)
        if not song:
            results = await db.search_songs(query_strip)
            if results:
                song = results[0]
        if not song:
            await interaction.followup.send(f"❌ Kein lokaler Titel gefunden: `{query_strip}`", ephemeral=True)
            return

        if radio.voice_channel_id is None:
            radio.dispatch(RadioAction.JOIN, interaction.user.voice.channel.id, user=interaction.user)
        radio.dispatch(RadioAction.ADD_TO_QUEUE, song, user=interaction.user)
        await interaction.followup.send(
            f"✅ AutoDJ-Queue: **{song.get('artist', 'Unknown')} – {song.get('title', 'Unknown')}**",
            ephemeral=True,
        )

    @tree.command(name="autodjstats", description="Zeigt die Wiedergabestatistik des lokalen AutoDJ")
    async def autodjstats(interaction: discord.Interaction):
        from ui_studio import StatsView

        await interaction.response.defer(ephemeral=True)
        days = 7
        top_artists = await db.get_top_artists(days=days)
        top_songs = await db.get_top_songs(days=days)
        top_users = await db.get_top_users(days=days)
        view = StatsView(
            radio,
            interaction.user,
            guild=interaction.guild,
            top_artists=top_artists,
            top_songs=top_songs,
            top_users=top_users,
        )
        await interaction.followup.send(view=view, ephemeral=True)

    @track.autocomplete("query")
    async def track_autocomplete(interaction: discord.Interaction, current: str):
        if not current or len(current) < 2:
            return []
        results = await db.search_songs(current)
        choices = []
        for song in results[: radio.config.autocomplete_limit]:
            label = f"{song['artist']} - {song['title']}"
            if len(label) > 100:
                label = label[:97] + "..."
            choices.append(app_commands.Choice(name=label, value=str(song["id"])))
        return choices
