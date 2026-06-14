"""666 RadioBotAI Lite — discord.py + FFmpeg + gTTS

Env-Vars (in Render setzen):
  DISCORD_TOKEN              Bot-Token (Discord Developer Portal)
  STREAM_URL                 Standard WebRadio-Stream-URL
  API_BASE_URL               URL des DJ-Panel API-Servers
  DEFAULT_VOICE_CHANNEL_ID   (optional) Standard Voice-Channel ID
  DISCORD_WELCOME_CHANNEL_ID (optional) Welcome-Channel für neue Member
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("radiobotai")

DISCORD_TOKEN               = os.getenv("DISCORD_TOKEN", "")
STREAM_URL                  = os.getenv("STREAM_URL", "")
API_BASE_URL                = os.getenv("API_BASE_URL", "").rstrip("/")
DEFAULT_VOICE_CHANNEL_ID    = int(os.getenv("DEFAULT_VOICE_CHANNEL_ID", "0") or "0")
WELCOME_CHANNEL_ID          = int(os.getenv("DISCORD_WELCOME_CHANNEL_ID", "0") or "0")
EMBED_COLOR                 = 0xFF00CC
PRESETS_FILE                = "presets.json"

# ── Built-in Presets ────────────────────────────────────────────────────────────
DEFAULT_PRESETS: dict[str, str] = {
    "666sounds": STREAM_URL,
    "soma-groovesalad": "https://ice1.somafm.com/groovesalad-256-mp3",
    "soma-dronezone":   "https://ice1.somafm.com/dronezone-256-mp3",
    "di-trance":        "https://di.fm/trance",
    "laut-psytrance":   "https://laut.fm/psytrance",
}


def _load_presets() -> dict[str, str]:
    try:
        if os.path.exists(PRESETS_FILE):
            with open(PRESETS_FILE) as f:
                return {**DEFAULT_PRESETS, **json.load(f)}
    except Exception:
        pass
    return {**DEFAULT_PRESETS}


def _save_presets(presets: dict[str, str]) -> None:
    try:
        custom = {k: v for k, v in presets.items() if k not in DEFAULT_PRESETS}
        with open(PRESETS_FILE, "w") as f:
            json.dump(custom, f, indent=2)
    except Exception as e:
        log.warning("Presets speichern fehlgeschlagen: %s", e)


PRESETS: dict[str, str] = _load_presets()


# ── Philosophie ─────────────────────────────────────────────────────────────────
PHILOSOPHY_TOPICS = {
    "dna": {
        "title": "🧬 Fraggle-DNA — Das Klanggenom", "color": 0x00FFD0,
        "fields": [
            ("Was ist Fraggle-DNA?",
             "Das persönliche Klanggenom von 666SOUNDsDESIGn:\n"
             "**dunkle Bunkerbasis · leuchtender Psytrance-Himmel · menschlicher Kern**", False),
            ("Die 5 Elemente",
             "🔴 **Druck** — Bass, Kick, Club-Impact\n"
             "🔵 **Tiefe** — Sub, Raum, Dunkelheit\n"
             "⚡ **Kontrolliertes Chaos** — Glitch, Acid\n"
             "🤖 **Cyberpunk** — Neon, digitale Seele\n"
             "❤️ **Human Core** — Der Mensch bleibt der Ursprung", False),
        ],
        "footer": "666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.",
    },
    "papaemds": {
        "title": "🏗️ P.A.P.A.E.M.D.S. — Die Architektur", "color": 0xFF00CC,
        "fields": [
            ("Formel", "```\nMensch gibt Bedeutung\n  ↓\nSystem gibt Struktur\n  ↓\nKlang gibt Return\n```", False),
        ],
        "footer": "P.A.P.A.E.M.D.S. — Human First",
    },
    "dynasty": {
        "title": "👑 Fraggle-Dynasty", "color": 0x9B00FF,
        "fields": [
            ("Figuren",
             "👤 Creator / FRAGGELPOWER666 · 🤖 Detlef / AI\n"
             "🚀 Captain · 🌌 Vessel · ⚡ Main Reactor · ☠️ Captain 666", False),
        ],
        "footer": "Bass · Bewusstsein · Widerstand · Freiheit",
    },
    "hierarchie": {
        "title": "⚡ System-Hierarchie", "color": 0xFF6600,
        "fields": [
            ("Stack", "```\n666 RadioBotAI        ← Gesamtchef\nStream 666 Design     ← Kreativer Chef\nCreator FRAGGELPOWER666 ← Der Ursprung\n```", False),
        ],
        "footer": "666SOUNDsDESIGn WebRadio · Fraggle DNA.",
    },
    "mantra": {
        "title": "🔮 Das Mantra", "color": 0x9B00FF,
        "fields": [
            ("EN / DE",
             "```\nThe Creator gives the spark.\nFraggle-DNA gives the living signature.\nSound becomes a room.\nThe human remains the origin.\n```"
             "```\nDer Creator gibt den Funken.\nFraggle-DNA gibt die lebende Signatur.\nKlang wird zum Raum. Der Mensch bleibt der Ursprung.\n```", False),
        ],
        "footer": "666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.",
    },
    "psychoakustik": {
        "title": "🎧 Psychoakustisches Musikdesign", "color": 0x00AAFF,
        "fields": [
            ("Kernfrage", "**Welche Wirkung soll im Menschen entstehen?**", False),
            ("Wirkungsfelder",
             "🥁 Kick — Körperanker · 🔊 Sub — Erdung · 🎵 Bassline — Trance\n"
             "🎤 Vocals — Menschlicher Kern · 💥 Drop — Entladung · 🔄 Loop — Ritual", False),
        ],
        "footer": "666SOUNDsDESIGn · Psychoakustisches Musikdesign",
    },
}


# ── RadioPlayer ──────────────────────────────────────────────────────────────────
class RadioPlayer:
    def __init__(self):
        self.voice_client: Optional[discord.VoiceClient] = None
        self._volume = 1.0
        self.current_url: Optional[str] = None
        self.current_name: Optional[str] = None

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, val: float):
        self._volume = max(0.0, min(2.0, val))
        if self.voice_client and self.voice_client.source:
            try:
                self.voice_client.source.volume = self._volume
            except Exception:
                pass

    def is_playing(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_playing())

    def is_connected(self) -> bool:
        return bool(self.voice_client and self.voice_client.is_connected())

    async def join(self, channel: discord.VoiceChannel) -> None:
        if self.voice_client and self.voice_client.is_connected():
            if self.voice_client.channel.id != channel.id:
                await self.voice_client.move_to(channel)
        else:
            self.voice_client = await channel.connect()

    async def play_stream(self, channel: discord.VoiceChannel, url: str, name: str = "Stream") -> None:
        await self.join(channel)
        if self.voice_client.is_playing():
            self.voice_client.stop()
        self.current_url = url
        self.current_name = name
        src = discord.FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn",
        )
        transformed = discord.PCMVolumeTransformer(src, volume=self._volume)
        self.voice_client.play(transformed, after=lambda e: log.error("FFmpeg: %s", e) if e else None)

    async def play_tts(self, channel: discord.VoiceChannel, audio_path: str) -> None:
        await self.join(channel)
        was_playing = self.voice_client.is_playing()
        if was_playing:
            self.voice_client.pause()
        src = discord.FFmpegPCMAudio(audio_path)
        transformed = discord.PCMVolumeTransformer(src, volume=min(self._volume * 1.5, 2.0))

        done = asyncio.Event()
        def after_tts(err):
            if err:
                log.error("TTS FFmpeg: %s", err)
            done.set()
            try:
                os.unlink(audio_path)
            except Exception:
                pass

        self.voice_client.play(transformed, after=after_tts)
        await done.wait()

        if was_playing and self.current_url:
            src2 = discord.FFmpegPCMAudio(
                self.current_url,
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                options="-vn",
            )
            self.voice_client.play(discord.PCMVolumeTransformer(src2, volume=self._volume))

    async def stop(self) -> None:
        self.current_url = None
        self.current_name = None
        if self.voice_client:
            if self.voice_client.is_playing():
                self.voice_client.stop()
            try:
                await self.voice_client.disconnect(force=True)
            except Exception:
                pass
            self.voice_client = None

    async def leave(self) -> None:
        await self.stop()


player = RadioPlayer()


# ── API helpers ──────────────────────────────────────────────────────────────────
async def api_get(path: str) -> dict:
    if not API_BASE_URL:
        return {}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{API_BASE_URL}{path}", timeout=aiohttp.ClientTimeout(total=6)) as r:
                return await r.json()
    except Exception as e:
        log.warning("API GET %s: %s", path, e)
        return {}


async def api_post(path: str, data: dict | None = None) -> dict:
    if not API_BASE_URL:
        return {}
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(f"{API_BASE_URL}{path}", json=data or {}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                return await r.json()
    except Exception as e:
        log.warning("API POST %s: %s", path, e)
        return {}


def radio_embed(title: str, desc: str = None) -> discord.Embed:
    e = discord.Embed(title=title, description=desc, color=EMBED_COLOR)
    e.set_footer(text="666 RadioBotAI · 666SOUNDsDESIGn · Fraggle DNA")
    return e


async def _resolve_vc(interaction: discord.Interaction, channel: Optional[discord.VoiceChannel] = None) -> Optional[discord.VoiceChannel]:
    if channel:
        return channel
    if interaction.user.voice and isinstance(interaction.user.voice.channel, discord.VoiceChannel):
        return interaction.user.voice.channel
    if DEFAULT_VOICE_CHANNEL_ID:
        ch = interaction.guild.get_channel(DEFAULT_VOICE_CHANNEL_ID)
        if isinstance(ch, discord.VoiceChannel):
            return ch
    return None


# ── Bot setup ────────────────────────────────────────────────────────────────────
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
    log.info("  Tag:     %s  |  ID: %s", bot.user, bot.user.id)
    log.info("══════════════════════════════════════════")
    try:
        synced = await bot.tree.sync()
        log.info("  Slash-Commands: %d synced", len(synced))
    except Exception as e:
        log.error("  Sync failed: %s", e)


@bot.event
async def on_member_join(member: discord.Member):
    ch = (member.guild.get_channel(WELCOME_CHANNEL_ID) if WELCOME_CHANNEL_ID else None) or member.guild.system_channel
    if not ch or not isinstance(ch, discord.TextChannel):
        return
    e = discord.Embed(
        title=f"⚡ Neue Frequenz erkannt — willkommen, {member.display_name}",
        description=(
            f"Du betrittst **666SOUNDsDESIGn WebRadio**.\n\n"
            f"Ich bin **666 RadioBotAI** — angetrieben von **Fraggle-DNA**:\n"
            f"> Druck · Tiefe · Chaos · Cyberpunk · Human Core\n\n"
            f"*Sound becomes a room. The human remains the origin.*"
        ),
        color=EMBED_COLOR,
    )
    e.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
    e.set_thumbnail(url=member.display_avatar.url)
    await ch.send(embed=e)


# ═══════════════════════════════════════════════════════════════════════════════
# /play  /join  /leave  /stop  /bye
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="play", description="Startet Radio-Stream. /play → Standard-Stream. /play <url> → beliebiger Stream. /play <preset-name> → gespeichertes Preset.")
@app_commands.describe(stream="Stream-URL oder Preset-Name (leer = Standard-Stream)")
async def cmd_play(interaction: discord.Interaction, stream: Optional[str] = None, channel: Optional[discord.VoiceChannel] = None):
    await interaction.response.defer()
    vc = await _resolve_vc(interaction, channel)
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel oder gib einen an.", ephemeral=True)

    url = None
    name = "Stream"

    if stream:
        if stream.startswith(("http://", "https://")):
            url = stream
            name = stream.split("/")[2]
        elif stream in PRESETS:
            url = PRESETS[stream]
            name = stream
        else:
            keys = [k for k in PRESETS if stream.lower() in k.lower()]
            if keys:
                url = PRESETS[keys[0]]
                name = keys[0]
            else:
                return await interaction.followup.send(
                    f"❌ `{stream}` ist keine gültige URL und kein bekanntes Preset.\n"
                    f"Presets: {', '.join(f'`{k}`' for k in PRESETS)}", ephemeral=True
                )
    else:
        url = STREAM_URL
        name = "666SOUNDsDESIGn"

    if not url:
        return await interaction.followup.send("⚠️ Keine Stream-URL konfiguriert.", ephemeral=True)

    try:
        await player.play_stream(vc, url, name)
    except Exception as exc:
        return await interaction.followup.send(f"❌ Stream-Fehler: `{exc}`", ephemeral=True)

    e = radio_embed("📻 Stream läuft", f"**{name}** läuft in {vc.mention}\nVolume: `{int(player.volume * 100)}%`")
    await interaction.followup.send(embed=e)


@bot.tree.command(name="join", description="Bot tritt dem Voice-Channel bei (ohne Stream zu starten)")
@app_commands.describe(channel="Voice-Channel (optional)")
async def cmd_join(interaction: discord.Interaction, channel: Optional[discord.VoiceChannel] = None):
    await interaction.response.defer()
    vc = await _resolve_vc(interaction, channel)
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel.", ephemeral=True)
    try:
        await player.join(vc)
    except Exception as exc:
        return await interaction.followup.send(f"❌ Join fehlgeschlagen: `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("🎙️ Joined", f"Verbunden mit {vc.mention} — bereit."))


@bot.tree.command(name="leave", description="Bot verlässt den Voice-Channel (Aliase: /stop /bye /cancel)")
async def cmd_leave(interaction: discord.Interaction):
    if not player.is_connected():
        return await interaction.response.send_message("Bot ist nicht verbunden.", ephemeral=True)
    await player.leave()
    await interaction.response.send_message(embed=radio_embed("👋 Tschüss", "Stream gestoppt, Voice verlassen."))


@bot.tree.command(name="stop", description="Stoppt den Stream und verlässt den Channel")
async def cmd_stop(interaction: discord.Interaction):
    await cmd_leave.callback(cmd_leave, interaction)


@bot.tree.command(name="bye", description="Verlässt den Voice-Channel")
async def cmd_bye(interaction: discord.Interaction):
    await cmd_leave.callback(cmd_leave, interaction)


# ═══════════════════════════════════════════════════════════════════════════════
# /say — TTS im Voice-Channel
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="say", description="Bot spricht einen Text im Voice-Channel (TTS)")
@app_commands.describe(text="Was der Bot sagen soll", lang="Sprache: de (Standard), en, fr, es ...")
async def cmd_say(interaction: discord.Interaction, text: str, lang: str = "de"):
    await interaction.response.defer(ephemeral=True)

    vc = await _resolve_vc(interaction)
    if not vc and player.voice_client:
        vc = player.voice_client.channel
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel.", ephemeral=True)

    try:
        from gtts import gTTS
    except ImportError:
        return await interaction.followup.send("⚠️ gTTS nicht installiert.", ephemeral=True)

    try:
        tts = gTTS(text=text[:500], lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            audio_path = f.name
    except Exception as exc:
        return await interaction.followup.send(f"❌ TTS-Fehler: `{exc}`", ephemeral=True)

    try:
        await player.play_tts(vc, audio_path)
    except Exception as exc:
        return await interaction.followup.send(f"❌ Abspielen fehlgeschlagen: `{exc}`", ephemeral=True)

    await interaction.followup.send(f"✅ Gesagt: *{text[:100]}*", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
# /preset — Stream-Presets verwalten
# ═══════════════════════════════════════════════════════════════════════════════

preset_group = app_commands.Group(name="preset", description="Radio-Stream Presets verwalten")


@preset_group.command(name="list", description="Zeigt alle gespeicherten Stream-Presets")
async def preset_list(interaction: discord.Interaction):
    if not PRESETS:
        return await interaction.response.send_message("Keine Presets gespeichert.", ephemeral=True)
    lines = [f"• `{name}` — {url}" for name, url in PRESETS.items()]
    e = radio_embed("📻 Stream-Presets", "\n".join(lines))
    await interaction.response.send_message(embed=e, ephemeral=True)


@preset_group.command(name="play", description="Spielt ein gespeichertes Preset ab")
@app_commands.describe(name="Preset-Name", channel="Voice-Channel (optional)")
async def preset_play(interaction: discord.Interaction, name: str, channel: Optional[discord.VoiceChannel] = None):
    await interaction.response.defer()
    if name not in PRESETS:
        return await interaction.followup.send(f"❌ Preset `{name}` nicht gefunden.\nVerfügbar: {', '.join(f'`{k}`' for k in PRESETS)}", ephemeral=True)
    vc = await _resolve_vc(interaction, channel)
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel.", ephemeral=True)
    try:
        await player.play_stream(vc, PRESETS[name], name)
    except Exception as exc:
        return await interaction.followup.send(f"❌ `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("📻 Preset spielt", f"**{name}** in {vc.mention}"))


@preset_group.command(name="add", description="Fügt ein neues Stream-Preset hinzu")
@app_commands.describe(name="Preset-Name (kurz, ohne Leerzeichen)", url="Stream-URL")
async def preset_add(interaction: discord.Interaction, name: str, url: str):
    if not url.startswith(("http://", "https://")):
        return await interaction.response.send_message("❌ URL muss mit http:// oder https:// beginnen.", ephemeral=True)
    name = name.lower().replace(" ", "-")[:30]
    PRESETS[name] = url
    _save_presets(PRESETS)
    await interaction.response.send_message(embed=radio_embed("✅ Preset gespeichert", f"`{name}` → {url}"), ephemeral=True)


@preset_group.command(name="remove", description="Löscht ein Preset")
@app_commands.describe(name="Preset-Name")
async def preset_remove(interaction: discord.Interaction, name: str):
    if name in DEFAULT_PRESETS:
        return await interaction.response.send_message("❌ Standard-Presets können nicht gelöscht werden.", ephemeral=True)
    if name not in PRESETS:
        return await interaction.response.send_message(f"❌ Preset `{name}` nicht gefunden.", ephemeral=True)
    del PRESETS[name]
    _save_presets(PRESETS)
    await interaction.response.send_message(f"✅ Preset `{name}` gelöscht.", ephemeral=True)


bot.tree.add_command(preset_group)


# ═══════════════════════════════════════════════════════════════════════════════
# /radio — Stream-Steuerung
# ═══════════════════════════════════════════════════════════════════════════════

radio_group = app_commands.Group(name="radio", description="666 RadioBotAI Stream-Steuerung")


@radio_group.command(name="skip", description="Überspringt den aktuellen Song")
async def radio_skip(interaction: discord.Interaction):
    await interaction.response.defer()
    r = await api_post("/skip")
    if r.get("success"):
        await interaction.followup.send(embed=radio_embed("⏭️ Song übersprungen", r.get("skipNote")))
    else:
        await interaction.followup.send(f"❌ Skip fehlgeschlagen: `{r.get('error', '?')}`", ephemeral=True)


@radio_group.command(name="voteskip", description="Vote-to-Skip abstimmen")
async def radio_voteskip(interaction: discord.Interaction):
    await interaction.response.defer()
    r = await api_post("/skip/vote", {"voterId": str(interaction.user.id)})
    votes, threshold = r.get("votes", 0), r.get("threshold", 3)
    if r.get("shouldSkip"):
        await api_post("/skip")
        await interaction.followup.send(embed=radio_embed("⏭️ Vote-Skip", f"Genug Stimmen! [{votes}/{threshold}]"))
    else:
        await interaction.followup.send(embed=radio_embed("🗳️ Vote", f"**{votes}/{threshold}** — {threshold-votes} mehr nötig."))


@radio_group.command(name="nowplaying", description="Aktuell laufender Song")
async def radio_np(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    s = await api_get("/stream/status")
    if not s or not s.get("isOnline"):
        return await interaction.followup.send(embed=radio_embed("📻 Now Playing", "Stream offline."), ephemeral=True)
    song = s.get("currentSong") or "Unbekannt"
    desc = f"**{song}**\n👥 `{s.get('listeners',0)}` Hörer"
    if s.get("bitrate"):
        desc += f" · 🎚️ `{s['bitrate']} kbps`"
    await interaction.followup.send(embed=radio_embed("🎵 Now Playing", desc), ephemeral=True)


@radio_group.command(name="status", description="Vollständiger RadioBotAI-Status")
async def radio_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    s = await api_get("/stream/status")
    e = radio_embed("666 RadioBotAI Status")
    e.add_field(name="Voice", value=(f"▶️ {player.voice_client.channel.mention}" if player.is_connected() else "Nicht verbunden"), inline=False)
    e.add_field(name="Playback", value="▶️ Läuft" if player.is_playing() else "⏹️ Stop", inline=True)
    e.add_field(name="Volume", value=f"`{int(player.volume*100)}%`", inline=True)
    if player.current_name:
        e.add_field(name="Preset", value=f"`{player.current_name}`", inline=True)
    if s:
        e.add_field(name="Stream", value="🟢 Online" if s.get("isOnline") else "🔴 Offline", inline=False)
        e.add_field(name="Song", value=f"`{s.get('currentSong') or '—'}`", inline=False)
        e.add_field(name="Hörer", value=f"`{s.get('listeners',0)}`", inline=True)
    await interaction.followup.send(embed=e, ephemeral=True)


@radio_group.command(name="volume", description="Lautstärke setzen (0–200)")
@app_commands.describe(value="Lautstärke in Prozent")
async def radio_volume(interaction: discord.Interaction, value: app_commands.Range[int, 0, 200]):
    player.volume = value / 100.0
    await interaction.response.send_message(embed=radio_embed("🔊 Volume", f"`{value}%`"), ephemeral=True)


@radio_group.command(name="repair", description="Stream neu starten")
async def radio_repair(interaction: discord.Interaction):
    await interaction.response.defer()
    url = player.current_url or STREAM_URL
    if not url:
        return await interaction.followup.send("⚠️ Keine Stream-URL.", ephemeral=True)
    vc = player.voice_client.channel if player.is_connected() else await _resolve_vc(interaction)
    if not vc:
        return await interaction.followup.send("⚠️ Kein Voice-Channel.", ephemeral=True)
    await player.stop()
    await asyncio.sleep(1)
    try:
        await player.play_stream(vc, url, player.current_name or "Stream")
    except Exception as exc:
        return await interaction.followup.send(f"❌ `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("🛠️ Repair", f"Neugestartet in {vc.mention}"))


@radio_group.command(name="history", description="Zuletzt gespielte Songs")
async def radio_history(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    h = await api_get("/history")
    if not h or not isinstance(h, list):
        return await interaction.followup.send(embed=radio_embed("📜 History", "Keine History."), ephemeral=True)
    lines = [f"`{i}.` {(e.get('artist') or '')} — {(e.get('title') or '')}".strip(" —") for i, e in enumerate(h[:10], 1)]
    await interaction.followup.send(embed=radio_embed("📜 Zuletzt gespielt", "\n".join(lines)), ephemeral=True)


bot.tree.add_command(radio_group)


# ═══════════════════════════════════════════════════════════════════════════════
# /identity + /philosophy
# ═══════════════════════════════════════════════════════════════════════════════

@bot.tree.command(name="identity", description="666 RadioBotAI Identität — Fraggle-DNA")
async def identity(interaction: discord.Interaction):
    e = discord.Embed(
        title="⚡ 666 RadioBotAI — Wer ich bin",
        description="Ich bin **666 RadioBotAI** — Gesamtchef des 666SOUNDsDESIGn Systems.\nMein Antrieb ist reine **Fraggle-DNA**.",
        color=EMBED_COLOR,
    )
    e.add_field(name="🧬 DNA", value="🔴 Druck · 🔵 Tiefe · ⚡ Chaos · 🤖 Cyberpunk · ❤️ Human Core", inline=False)
    e.add_field(name="👑 Hierarchie", value="```\n666 RadioBotAI     ← Gesamtchef\nStream 666 Design  ← Kreativer Chef\nFRAGGELPOWER666   ← Creator\n```", inline=False)
    e.set_footer(text="Fraggle DNA. Alive in the frequency. · /philosophy für mehr")
    await interaction.response.send_message(embed=e)


philosophy_group = app_commands.Group(name="philosophy", description="Fraggle-DNA Philosophie")


@philosophy_group.command(name="liste", description="Alle Philosophie-Themen")
async def philosophy_liste(interaction: discord.Interaction):
    topics = "\n".join(f"• `/philosophy {k}` — {v['title']}" for k, v in PHILOSOPHY_TOPICS.items())
    e = discord.Embed(title="📖 Philosophie der 666SOUNDsDESIGn Dynasty", description=topics, color=EMBED_COLOR)
    e.set_footer(text="666SOUNDsDESIGn · Fraggle DNA.")
    await interaction.response.send_message(embed=e)


def _make_topic_cmd(key: str):
    data = PHILOSOPHY_TOPICS[key]
    async def _cmd(interaction: discord.Interaction):
        e = discord.Embed(title=data["title"], color=data["color"])
        for name, value, inline in data["fields"]:
            e.add_field(name=name, value=value, inline=inline)
        e.set_footer(text=data.get("footer", "666SOUNDsDESIGn"))
        await interaction.response.send_message(embed=e)
    _cmd.__name__ = f"philosophy_{key}"
    return _cmd


for _key, _data in PHILOSOPHY_TOPICS.items():
    philosophy_group.add_command(
        app_commands.command(name=_key, description=_data["title"])(_make_topic_cmd(_key))
    )

bot.tree.add_command(philosophy_group)


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN ist nicht gesetzt!")
    if not STREAM_URL:
        log.warning("STREAM_URL nicht gesetzt — /play ohne Argument funktioniert nicht")
    bot.run(DISCORD_TOKEN)
