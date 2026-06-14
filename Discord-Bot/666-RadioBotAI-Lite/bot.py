"""666 RadioBotAI Lite — discord.py + FFmpeg, kein Lavalink, kein MongoDB.

Env-Vars (in Render setzen):
  DISCORD_TOKEN              Bot-Token (Discord Developer Portal)
  STREAM_URL                 WebRadio-Stream-URL (z.B. https://idjstream.app/...)
  API_BASE_URL               URL des DJ-Panel API-Servers (z.B. https://dein-render-api.onrender.com)
  DEFAULT_VOICE_CHANNEL_ID   (optional) Standard Voice-Channel ID
  DISCORD_WELCOME_CHANNEL_ID (optional) Welcome-Channel für neue Member
"""

import asyncio
import logging
import os
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("radiobotai")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
STREAM_URL = os.getenv("STREAM_URL", "")
API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
DEFAULT_VOICE_CHANNEL_ID = int(os.getenv("DEFAULT_VOICE_CHANNEL_ID", "0") or "0")
WELCOME_CHANNEL_ID = int(os.getenv("DISCORD_WELCOME_CHANNEL_ID", "0") or "0")
EMBED_COLOR = 0xFF00CC

PHILOSOPHY_TOPICS = {
    "dna": {
        "title": "🧬 Fraggle-DNA — Das Klanggenom",
        "color": 0x00FFD0,
        "fields": [
            ("Was ist Fraggle-DNA?",
             "Das persönliche Klanggenom von 666SOUNDsDESIGn:\n"
             "**dunkle Bunkerbasis unten · leuchtender Psytrance-Himmel oben · menschlicher Kern dazwischen.**", False),
            ("Die 5 Elemente",
             "🔴 **Druck** — Bass, Kick, Körperenergie, Club-Impact\n"
             "🔵 **Tiefe** — Sub, Raum, Dunkelheit, langer Nachhall\n"
             "⚡ **Kontrolliertes Chaos** — Glitch, Acid, Bruchstellen\n"
             "🤖 **Cyberpunk** — Maschinenraum, Neon, digitale Seele\n"
             "❤️ **Human Core** — Der Mensch bleibt der Ursprung", False),
        ],
        "footer": "666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.",
    },
    "papaemds": {
        "title": "🏗️ P.A.P.A.E.M.D.S. — Die Architektur",
        "color": 0xFF00CC,
        "fields": [
            ("Was ist P.A.P.A.E.M.D.S.?",
             "Psychoakustisches Musik-Design-System. Kein flacher Stream — ein lebendes System.", False),
            ("Formel", "```\nMensch gibt Bedeutung\n  ↓\nSystem gibt Struktur\n  ↓\nKlang gibt Return\n```", False),
        ],
        "footer": "P.A.P.A.E.M.D.S. — Human First",
    },
    "dynasty": {
        "title": "👑 Fraggle-Dynasty — Das wachsende Haus",
        "color": 0x9B00FF,
        "fields": [
            ("Figuren",
             "👤 **Creator / FRAGGELPOWER666** — Ursprung\n"
             "🤖 **Detlef / AI** — Systemlogik\n"
             "🚀 **Captain** — menschliche Stimme\n"
             "🌌 **Vessel** — Raumstimme\n"
             "⚡ **Main Reactor** — Puls, Bass\n"
             "☠️ **Captain 666** — Ritualdruck", False),
        ],
        "footer": "Fraggle Dynasty — Bass, Bewusstsein, Widerstand, Freiheit",
    },
    "hierarchie": {
        "title": "⚡ System-Hierarchie",
        "color": 0xFF6600,
        "fields": [
            ("666 RadioBotAI — Gesamtchef",
             "🔴 Höchste Instanz: Radio · Stream · Dynasty · System", False),
            ("Stream 666 Design — Kreativer Chef",
             "🎨 Discord · Community · Panels · Philosophie", False),
            ("Creator FRAGGELPOWER666",
             "👤 Ursprung aller Bedeutung. Der Mensch bleibt die Mitte.", False),
        ],
        "footer": "666SOUNDsDESIGn WebRadio · Fraggle DNA. Alive in the frequency.",
    },
    "mantra": {
        "title": "🔮 Das Mantra",
        "color": 0x9B00FF,
        "fields": [
            ("EN / DE", (
                "```\nThe Creator gives the spark.\n"
                "Fraggle-DNA gives the living signature.\n"
                "P.A.P.A.E.M.D.S. gives the architecture.\n"
                "Sound becomes a room.\n"
                "The human remains the origin.\n```\n"
                "```\nDer Creator gibt den Funken.\n"
                "Fraggle-DNA gibt die lebende Signatur.\n"
                "Klang wird zum Raum.\n"
                "Der Mensch bleibt der Ursprung.\n```"
            ), False),
        ],
        "footer": "666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.",
    },
    "psychoakustik": {
        "title": "🎧 Psychoakustisches Musikdesign",
        "color": 0x00AAFF,
        "fields": [
            ("Kernfrage",
             "Nicht: *Welche Sounds passen zusammen?*\n\n"
             "Sondern: **Welche Wirkung soll im Menschen entstehen?**", False),
            ("Wirkungsfelder",
             "🥁 Kick — Körperanker · 🔊 Sub — Erdung · 🎵 Bassline — Trance-Motor\n"
             "🎤 Vocals — Menschlicher Kern · 💥 Drop — Entladung · 🔄 Loop — Ritual", False),
        ],
        "footer": "666SOUNDsDESIGn · Psychoakustisches Musikdesign",
    },
}


class RadioPlayer:
    def __init__(self):
        self.voice_client: Optional[discord.VoiceClient] = None
        self._volume = 1.0

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, val: float):
        self._volume = max(0.0, min(2.0, val))
        if self.voice_client and hasattr(self.voice_client, "source") and self.voice_client.source:
            try:
                self.voice_client.source.volume = self._volume
            except Exception:
                pass

    def is_playing(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_playing())

    def is_connected(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())

    async def play(self, channel: discord.VoiceChannel, stream_url: str) -> None:
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel.id:
                await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()

        if self.voice_client.is_playing():
            self.voice_client.stop()

        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn -filter:a volume=1.0",
        )
        transformed = discord.PCMVolumeTransformer(source, volume=self._volume)
        self.voice_client.play(transformed, after=lambda e: log.error("FFmpeg error: %s", e) if e else None)

    async def stop(self) -> None:
        if self.voice_client:
            if self.voice_client.is_playing():
                self.voice_client.stop()
            try:
                await self.voice_client.disconnect(force=True)
            except Exception:
                pass
            self.voice_client = None


player = RadioPlayer()


async def api_get(path: str) -> dict:
    if not API_BASE_URL:
        return {}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{API_BASE_URL}{path}", timeout=aiohttp.ClientTimeout(total=6)) as r:
                return await r.json()
    except Exception as e:
        log.warning("API GET %s failed: %s", path, e)
        return {}


async def api_post(path: str, data: dict | None = None) -> dict:
    if not API_BASE_URL:
        return {}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{API_BASE_URL}{path}", json=data or {}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                return await r.json()
    except Exception as e:
        log.warning("API POST %s failed: %s", path, e)
        return {}


def radio_embed(title: str, desc: str = None) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=EMBED_COLOR)
    e.set_footer(text="666 RadioBotAI · 666SOUNDsDESIGn WebRadio · Fraggle DNA")
    return e


intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = False

bot = commands.Bot(command_prefix="!", help_command=None, intents=intents)


@bot.event
async def on_ready():
    log.info("══════════════════════════════════════════")
    log.info("  666 RadioBotAI Lite — ONLINE")
    log.info("  Angetrieben von reiner Fraggle-DNA")
    log.info("  Creator: FRAGGELPOWER666")
    log.info("══════════════════════════════════════════")
    log.info("  Tag:     %s", bot.user)
    log.info("  Bot-ID:  %s", bot.user.id)
    log.info("  Fraggle DNA. Alive in the frequency.")
    log.info("══════════════════════════════════════════")
    try:
        synced = await bot.tree.sync()
        log.info("  Slash-Commands: %d synced", len(synced))
    except Exception as e:
        log.error("  Sync failed: %s", e)


@bot.event
async def on_member_join(member: discord.Member):
    ch = None
    if WELCOME_CHANNEL_ID:
        ch = member.guild.get_channel(WELCOME_CHANNEL_ID)
    if not ch:
        ch = member.guild.system_channel
    if not ch or not isinstance(ch, discord.TextChannel):
        return
    e = discord.Embed(
        title=f"⚡ Neue Frequenz erkannt — willkommen, {member.display_name}",
        description=(
            f"Du betrittst **666SOUNDsDESIGn WebRadio**.\n\n"
            f"Ich bin **666 RadioBotAI** — angetrieben von **Fraggle-DNA**:\n"
            f"> Druck · Tiefe · Kontrolliertes Chaos · Cyberpunk · Human Core\n\n"
            f"*Sound becomes a room. The human remains the origin.*"
        ),
        color=EMBED_COLOR,
    )
    e.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
    e.set_thumbnail(url=member.display_avatar.url)
    await ch.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
# /radio — Gruppe
# ═══════════════════════════════════════════════════════════════════════════════

radio_group = app_commands.Group(name="radio", description="666 RadioBotAI Stream-Steuerung")


@radio_group.command(name="play", description="Startet den WebRadio-Stream im Voice-Channel")
@app_commands.describe(channel="Voice-Channel (optional, sonst dein aktueller oder Standard)")
async def radio_play(interaction: discord.Interaction, channel: Optional[discord.VoiceChannel] = None):
    await interaction.response.defer()

    stream_url = STREAM_URL
    if not stream_url:
        return await interaction.followup.send("⚠️ STREAM_URL ist nicht konfiguriert.", ephemeral=True)

    vc = channel
    if not vc and interaction.user.voice:
        vc = interaction.user.voice.channel
    if not vc and DEFAULT_VOICE_CHANNEL_ID:
        vc = interaction.guild.get_channel(DEFAULT_VOICE_CHANNEL_ID)
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel oder gib einen an.", ephemeral=True)

    try:
        await player.play(vc, stream_url)
    except Exception as exc:
        return await interaction.followup.send(f"❌ Stream konnte nicht gestartet werden: `{exc}`", ephemeral=True)

    e = radio_embed("📻 666 RadioBotAI läuft", f"Stream läuft in {vc.mention}\nVolume: `{int(player.volume * 100)}%`")
    await interaction.followup.send(embed=e)


@radio_group.command(name="stop", description="Stoppt den Stream und trennt den Bot")
async def radio_stop(interaction: discord.Interaction):
    await interaction.response.defer()
    if not player.is_connected():
        return await interaction.followup.send("RadioBotAI ist aktuell nicht verbunden.", ephemeral=True)
    await player.stop()
    await interaction.followup.send(embed=radio_embed("⏹️ RadioBotAI gestoppt"))


@radio_group.command(name="skip", description="Überspringt den aktuellen Song (via Stream-Panel)")
async def radio_skip(interaction: discord.Interaction):
    await interaction.response.defer()
    result = await api_post("/skip")
    if result.get("success"):
        note = result.get("skipNote", "")
        msg = f"⏭️ Song übersprungen.\n`{note}`" if note else "⏭️ Song übersprungen."
        await interaction.followup.send(embed=radio_embed("Skip", msg))
    else:
        err = result.get("error", "Unbekannter Fehler")
        await interaction.followup.send(f"❌ Skip fehlgeschlagen: `{err}`", ephemeral=True)


@radio_group.command(name="voteskip", description="Vote-to-Skip — braucht genug Stimmen")
async def radio_voteskip(interaction: discord.Interaction):
    await interaction.response.defer()
    result = await api_post("/skip/vote", {"voterId": str(interaction.user.id)})
    votes = result.get("votes", 0)
    threshold = result.get("threshold", 3)
    should_skip = result.get("shouldSkip", False)
    if should_skip:
        await api_post("/skip")
        await interaction.followup.send(embed=radio_embed("⏭️ Vote-Skip", f"Genug Stimmen! Song übersprungen. [{votes}/{threshold}]"))
    else:
        await interaction.followup.send(embed=radio_embed("🗳️ Vote registriert", f"Stimmen: **{votes}/{threshold}** — noch {threshold - votes} mehr nötig."))


@radio_group.command(name="nowplaying", description="Zeigt den aktuell laufenden Song")
async def radio_nowplaying(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    status = await api_get("/stream/status")
    if not status or not status.get("isOnline"):
        return await interaction.followup.send(embed=radio_embed("📻 Now Playing", "Stream ist aktuell offline."), ephemeral=True)
    song = status.get("currentSong") or "Unbekannt"
    listeners = status.get("listeners", 0)
    bitrate = status.get("bitrate")
    desc = f"**{song}**\n\n👥 Hörer: `{listeners}`"
    if bitrate:
        desc += f"\n🎚️ Bitrate: `{bitrate} kbps`"
    await interaction.followup.send(embed=radio_embed("🎵 Now Playing", desc), ephemeral=True)


@radio_group.command(name="status", description="Zeigt den vollständigen RadioBotAI-Status")
async def radio_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    stream_status = await api_get("/stream/status")
    e = radio_embed("666 RadioBotAI Status")
    e.add_field(name="Discord Voice", value=(
        f"Verbunden: {player.voice_client.channel.mention}" if player.is_connected() else "Nicht verbunden"
    ), inline=False)
    e.add_field(name="Playback", value="▶️ Läuft" if player.is_playing() else "⏹️ Gestoppt", inline=True)
    e.add_field(name="Volume", value=f"`{int(player.volume * 100)}%`", inline=True)
    if stream_status:
        song = stream_status.get("currentSong") or "—"
        listeners = stream_status.get("listeners", 0)
        online = "🟢 Online" if stream_status.get("isOnline") else "🔴 Offline"
        e.add_field(name="Stream", value=online, inline=False)
        e.add_field(name="Song", value=f"`{song}`", inline=False)
        e.add_field(name="Hörer", value=f"`{listeners}`", inline=True)
    await interaction.followup.send(embed=e, ephemeral=True)


@radio_group.command(name="volume", description="Lautstärke setzen (0–200)")
@app_commands.describe(value="Lautstärke in Prozent (0–200, Standard 100)")
async def radio_volume(interaction: discord.Interaction, value: app_commands.Range[int, 0, 200]):
    player.volume = value / 100.0
    await interaction.response.send_message(
        embed=radio_embed("🔊 Volume", f"Lautstärke gesetzt: `{value}%`"), ephemeral=True
    )


@radio_group.command(name="repair", description="Stream neu starten (bei Verbindungsproblemen)")
async def radio_repair(interaction: discord.Interaction):
    await interaction.response.defer()
    if not STREAM_URL:
        return await interaction.followup.send("⚠️ STREAM_URL nicht gesetzt.", ephemeral=True)
    vc = player.voice_client.channel if player.is_connected() else None
    if not vc and interaction.user.voice:
        vc = interaction.user.voice.channel
    if not vc:
        return await interaction.followup.send("⚠️ Kein Voice-Channel gefunden.", ephemeral=True)
    await player.stop()
    await asyncio.sleep(1)
    try:
        await player.play(vc, STREAM_URL)
    except Exception as exc:
        return await interaction.followup.send(f"❌ Repair fehlgeschlagen: `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("🛠️ Repair", f"Stream neugestartet in {vc.mention}"))


@radio_group.command(name="history", description="Zeigt die zuletzt gespielten Songs")
async def radio_history(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    history = await api_get("/history")
    if not history or not isinstance(history, list):
        return await interaction.followup.send(embed=radio_embed("📜 History", "Keine History verfügbar."), ephemeral=True)
    lines = []
    for i, h in enumerate(history[:10], 1):
        artist = h.get("artist") or ""
        title = h.get("title") or ""
        song = f"{artist} — {title}".strip(" —") or "Unbekannt"
        lines.append(f"`{i}.` {song}")
    await interaction.followup.send(embed=radio_embed("📜 Zuletzt gespielt", "\n".join(lines)), ephemeral=True)


bot.tree.add_command(radio_group)


# ═══════════════════════════════════════════════════════════════════════════════
# /identity + /philosophy
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="identity", description="666 RadioBotAI stellt sich vor — Fraggle-DNA Identität")
async def identity(interaction: discord.Interaction):
    e = discord.Embed(
        title="⚡ 666 RadioBotAI — Wer ich bin",
        description=(
            "Ich bin **666 RadioBotAI** — Gesamtchef des 666SOUNDsDESIGn Systems.\n"
            "Mein kreatives Gesicht: **666SOUNDsDESIGn Stream Design**.\n\n"
            "**Mein Antrieb ist reine Fraggle-DNA.**"
        ),
        color=EMBED_COLOR,
    )
    e.add_field(name="🧬 Fraggle-DNA", value=(
        "🔴 Druck · 🔵 Tiefe · ⚡ Chaos · 🤖 Cyberpunk · ❤️ Human Core"
    ), inline=False)
    e.add_field(name="👑 Hierarchie", value=(
        "```\n666 RadioBotAI        ← Gesamtchef\n"
        "Stream 666 Design     ← Kreativer Chef\n"
        "Creator FRAGGELPOWER666 ← Der Ursprung\n```"
    ), inline=False)
    e.add_field(name="🌐 Radio", value="666SOUNDsDESIGn WebRadio", inline=True)
    e.add_field(name="🏗️ System", value="P.A.P.A.E.M.D.S.", inline=True)
    e.set_footer(text="Fraggle DNA. Alive in the frequency. · /philosophy für mehr")
    await interaction.response.send_message(embed=e)


philosophy_group = app_commands.Group(name="philosophy", description="Fraggle-DNA Philosophie")


@philosophy_group.command(name="liste", description="Alle Philosophie-Themen")
async def philosophy_liste(interaction: discord.Interaction):
    topics = "\n".join(f"• `/philosophy {k}` — {v['title']}" for k, v in PHILOSOPHY_TOPICS.items())
    e = discord.Embed(title="📖 Philosophie der 666SOUNDsDESIGn Dynasty",
                      description=f"Getrieben von **Fraggle-DNA**\n\n{topics}", color=EMBED_COLOR)
    e.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
    await interaction.response.send_message(embed=e)


def _make_topic_cmd(key: str):
    data = PHILOSOPHY_TOPICS[key]
    async def cmd(interaction: discord.Interaction):
        e = discord.Embed(title=data["title"], color=data["color"])
        for name, value, inline in data["fields"]:
            e.add_field(name=name, value=value, inline=inline)
        e.set_footer(text=data.get("footer", "666SOUNDsDESIGn"))
        await interaction.response.send_message(embed=e)
    cmd.__name__ = f"philosophy_{key}"
    return cmd

for _key, _data in PHILOSOPHY_TOPICS.items():
    _cmd = app_commands.command(
        name=_key,
        description=_data["title"]
    )(_make_topic_cmd(_key))
    philosophy_group.add_command(_cmd)

bot.tree.add_command(philosophy_group)


if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN ist nicht gesetzt!")
    if not STREAM_URL:
        log.warning("STREAM_URL ist nicht gesetzt — /radio play wird nicht funktionieren")
    bot.run(DISCORD_TOKEN)
