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
API_BASE_URL                = os.getenv("API_BASE_URL", "").rstrip("/")
ALERT_API_URL               = os.getenv("ALERT_API_URL", "").rstrip("/")
ALERT_CHANNEL_ID            = int(os.getenv("ALERT_CHANNEL_ID", "0") or "0")
DEFAULT_VOICE_CHANNEL_ID    = int(os.getenv("DEFAULT_VOICE_CHANNEL_ID", "0") or "0")
WELCOME_CHANNEL_ID          = int(os.getenv("DISCORD_WELCOME_CHANNEL_ID", "0") or "0")
EMBED_COLOR                 = 0xFF00CC
PRESETS_FILE                = "presets.json"
WEBRADIO_URL                = "https://webradio.666soundsdesign-broadcaster.com"

# ── Stream Preset URLs (Render ENV-Vars mit echten Fallback-URLs) ─────────────────
# ENV-Vars setzen in Render → Environment (überschreiben die Defaults):
#   STREAM_MAIN_URL          → Hauptstream
#   STREAM_BACKUP_URL        → Backupstream / Backstream
#   STREAM_BACKUP_ALT_URL    → Backupstream Alt (Fallback)
#   STREAM_DOMAIN_STREAM_URL → Domain Stream via Cloudflare
#   STREAM_HEALING_URL       → Healing / Recovery-Modus (noch Platzhalter)
#   STREAM_THE_BACK_URL      → The Back (noch Platzhalter)
# STREAM_URL bleibt als Fallback für STREAM_MAIN_URL (Rückwärtskompatibilität)
_STREAM_MAIN_URL          = os.getenv("STREAM_MAIN_URL")          or os.getenv("STREAM_URL", "https://my.idjstream.com/666soundsdesign/stream")
_STREAM_BACKUP_URL        = os.getenv("STREAM_BACKUP_URL",        "https://my.idjstream.com:8686/stream")
_STREAM_BACKUP_ALT_URL    = os.getenv("STREAM_BACKUP_ALT_URL",    "https://my.idjstream.com/8686/stream")
_STREAM_DOMAIN_STREAM_URL = os.getenv("STREAM_DOMAIN_STREAM_URL", "https://webradio.666soundsdesign-broadcaster.com/stream")
_STREAM_HEALING_URL       = os.getenv("STREAM_HEALING_URL",       "")   # TODO: echte URL eintragen
_STREAM_THE_BACK_URL      = os.getenv("STREAM_THE_BACK_URL",      "")   # TODO: echte URL eintragen
STREAM_URL                = _STREAM_MAIN_URL  # Rückwärtskompatibilität
WEBRADIO_PLAYER_URL       = "https://webradio.666soundsdesign-broadcaster.com"
TUNEIN_URL                = "https://tunein.com/radio/s357001"

# Preset-Metadaten: id → (label, url, emoji, beschreibung)
_PRESET_META: dict[str, tuple[str, str, str, str]] = {
    "main":          ("Hauptstream",     _STREAM_MAIN_URL,          "🔴", "Hauptstream / MAIN — idjstream.com"),
    "backup":        ("Backupstream",    _STREAM_BACKUP_URL,        "🟡", "Backup-/Backstream — Port 8686"),
    "backup_alt":    ("Backup Alt",      _STREAM_BACKUP_ALT_URL,    "🟠", "Backupstream Alt — Fallback"),
    "domain_stream": ("Domain Stream",   _STREAM_DOMAIN_STREAM_URL, "🌐", "Stream via Cloudflare Domain"),
    "healing":       ("Healing",         _STREAM_HEALING_URL,       "🩵", "Healing / Recovery-Modus (Platzhalter)"),
    "theback":       ("The Back",        _STREAM_THE_BACK_URL,      "🟣", "The Back — separater Preset-Modus (Platzhalter)"),
}

# ── Built-in Presets (für /preset liste / /play) ─────────────────────────────────
# Nur Presets mit konfigurierter URL werden als aktiv gelistet.
DEFAULT_PRESETS: dict[str, str] = {
    k: v[1] for k, v in _PRESET_META.items() if v[1]
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
    asyncio.create_task(_messenger_poll_loop())


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
    e = radio_embed("📻 666SOUNDsDESIGn Stream-Presets")
    # Built-in 666SOUNDs presets
    for pid, (label, url, emoji, desc) in _PRESET_META.items():
        status = f"`{url}`" if url else "⚠️ *Noch nicht konfiguriert — ENV fehlt*"
        e.add_field(name=f"{emoji} {label} (`{pid}`)", value=f"{desc}\n{status}", inline=False)
    # Custom user-added presets
    custom = {k: v for k, v in PRESETS.items() if k not in _PRESET_META}
    if custom:
        e.add_field(name="─── Eigene Presets ───", value="\u200b", inline=False)
        for name, url in custom.items():
            e.add_field(name=f"• `{name}`", value=url, inline=False)
    e.add_field(
        name="🌐 WebRadio",
        value=f"[{WEBRADIO_URL}]({WEBRADIO_URL})",
        inline=False,
    )
    e.set_footer(text="ENV setzen in Render: STREAM_MAIN_URL · STREAM_BACKUP_URL · STREAM_HEALING_URL · STREAM_THE_BACK_URL")
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
    e = radio_embed("⚡ 666 RadioBotAI — System Status")

    # Voice / Playback
    e.add_field(name="🎙️ Voice",    value=(f"▶️ {player.voice_client.channel.mention}" if player.is_connected() else "Nicht verbunden"), inline=True)
    e.add_field(name="▶️ Playback", value="▶️ Läuft" if player.is_playing() else "⏹️ Stop", inline=True)
    e.add_field(name="🔊 Volume",   value=f"`{int(player.volume*100)}%`", inline=True)

    if player.current_name:
        e.add_field(name="📻 Aktives Preset", value=f"`{player.current_name}`", inline=False)

    # Stream-Status vom API
    if s:
        e.add_field(name="🌐 Stream",   value="🟢 Online" if s.get("isOnline") else "🔴 Offline", inline=True)
        e.add_field(name="👥 Hörer",    value=f"`{s.get('listeners', 0)}`", inline=True)
        e.add_field(name="🎚️ Bitrate",  value=f"`{s.get('bitrate', '—')} kbps`", inline=True)
        e.add_field(name="🎵 Song",     value=f"`{s.get('currentSong') or '—'}`", inline=False)

    # Preset-Konfigurationsstatus
    preset_lines = []
    for pid, (label, url, emoji, _) in _PRESET_META.items():
        state = "✅" if url else "⚠️"
        preset_lines.append(f"{state} {emoji} **{label}** (`{pid}`)")
    e.add_field(name="📋 Preset-Konfiguration", value="\n".join(preset_lines), inline=False)

    e.add_field(name="🌐 WebRadio", value=f"[{WEBRADIO_URL}]({WEBRADIO_URL})", inline=False)
    e.set_footer(text="666SOUNDsDESIGn · Fraggle DNA. Alive in the frequency.")
    await interaction.followup.send(embed=e, ephemeral=True)


@radio_group.command(name="volume", description="Lautstärke setzen (0–200)")
@app_commands.describe(value="Lautstärke in Prozent")
async def radio_volume(interaction: discord.Interaction, value: app_commands.Range[int, 0, 200]):
    player.volume = value / 100.0
    await interaction.response.send_message(embed=radio_embed("🔊 Volume", f"`{value}%`"), ephemeral=True)


@radio_group.command(name="repair", description="Stream neu starten (Repair / Reconnect)")
async def radio_repair(interaction: discord.Interaction):
    await interaction.response.defer()
    url  = player.current_url or _STREAM_MAIN_URL
    name = player.current_name or "Hauptstream"
    if not url:
        return await interaction.followup.send("⚠️ Keine Stream-URL konfiguriert (STREAM_MAIN_URL fehlt).", ephemeral=True)
    vc = player.voice_client.channel if player.is_connected() else await _resolve_vc(interaction)
    if not vc:
        return await interaction.followup.send("⚠️ Kein Voice-Channel.", ephemeral=True)
    await player.stop()
    await asyncio.sleep(1)
    try:
        await player.play_stream(vc, url, name)
    except Exception as exc:
        return await interaction.followup.send(f"❌ `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("🔄 Reconnect", f"**{name}** neu gestartet in {vc.mention}"))


@radio_group.command(name="reconnect", description="Aktuellen Stream kontrolliert neu verbinden")
async def radio_reconnect(interaction: discord.Interaction):
    """Alias for repair — reconnects the current stream without changing preset."""
    await radio_repair.callback(radio_repair, interaction)


@radio_group.command(name="reset", description="Player-Status zurücksetzen (kein Stream-Start)")
async def radio_reset(interaction: discord.Interaction):
    """Resets player state cleanly — stops stream, clears status, stays in channel."""
    await interaction.response.defer()
    was_playing = player.is_playing()
    was_connected = player.is_connected()
    channel_mention = player.voice_client.channel.mention if was_connected else "–"
    await player.stop()
    # Don't leave the channel — just stop playback and clear state
    e = radio_embed("🔁 Reset", "Player-Status zurückgesetzt.")
    e.add_field(name="War aktiv",     value="Ja" if was_playing else "Nein", inline=True)
    e.add_field(name="Voice-Channel", value=channel_mention,                 inline=True)
    e.add_field(
        name="Nächste Schritte",
        value=f"• `/play` — Hauptstream starten\n• `/radio reconnect` — Letzten Stream wiederherstellen\n• `/preset play main` — Explizit MAIN starten",
        inline=False,
    )
    e.set_footer(text="Keine Config, keine Presets, keine ENV-Vars wurden verändert.")
    await interaction.followup.send(embed=e)


@radio_group.command(name="main", description="Sofort auf Hauptstream schalten (MAIN)")
async def radio_main(interaction: discord.Interaction):
    """Quick-switch to MAIN preset — H-Button equivalent."""
    await interaction.response.defer()
    if not _STREAM_MAIN_URL:
        return await interaction.followup.send("⚠️ STREAM_MAIN_URL nicht konfiguriert.", ephemeral=True)
    vc = player.voice_client.channel if player.is_connected() else await _resolve_vc(interaction)
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel.", ephemeral=True)
    await player.stop()
    await asyncio.sleep(0.5)
    try:
        await player.play_stream(vc, _STREAM_MAIN_URL, "Hauptstream")
    except Exception as exc:
        return await interaction.followup.send(f"❌ `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("🔴 MAIN", f"Hauptstream läuft in {vc.mention}"))


@radio_group.command(name="backup", description="Sofort auf Backupstream schalten (BACKUP)")
async def radio_backup(interaction: discord.Interaction):
    """Quick-switch to BACKUP preset — B-Button equivalent."""
    await interaction.response.defer()
    if not _STREAM_BACKUP_URL:
        return await interaction.followup.send("⚠️ STREAM_BACKUP_URL nicht konfiguriert.", ephemeral=True)
    vc = player.voice_client.channel if player.is_connected() else await _resolve_vc(interaction)
    if not vc:
        return await interaction.followup.send("⚠️ Geh in einen Voice-Channel.", ephemeral=True)
    await player.stop()
    await asyncio.sleep(0.5)
    try:
        await player.play_stream(vc, _STREAM_BACKUP_URL, "Backupstream")
    except Exception as exc:
        return await interaction.followup.send(f"❌ `{exc}`", ephemeral=True)
    await interaction.followup.send(embed=radio_embed("🟡 BACKUP", f"Backupstream läuft in {vc.mention}"))


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
# MESSENGER — Dashboard ↔ Discord via Player Alert Relay
# Env-Vars: ALERT_API_URL, ALERT_CHANNEL_ID
# ═══════════════════════════════════════════════════════════════════════════════

_alert_seen_ids: set[str] = set()


def _find_best_text_channel(guild: discord.Guild) -> Optional[discord.TextChannel]:
    """
    Find the best text channel to post a dashboard alert into.

    Priority:
    1. Text channel in the same category as the voice channel where the bot is playing.
    2. First sendable text channel in any category that has a voice channel with the bot.
    3. Guild system channel.
    4. ALERT_CHANNEL_ID fallback (if configured).
    5. First sendable text channel in the guild.
    """
    # Is the bot in a voice channel in this guild?
    bot_vc: Optional[discord.VoiceChannel] = None
    if guild.voice_client and guild.voice_client.channel:
        bot_vc = guild.voice_client.channel  # type: ignore

    if bot_vc:
        # 1. Text channels in the same category, prefer one with "radio", "musik", "bot" in name
        category = bot_vc.category
        if category:
            text_channels = [c for c in category.channels if isinstance(c, discord.TextChannel) and c.permissions_for(guild.me).send_messages]
            if text_channels:
                preferred = next((c for c in text_channels if any(k in c.name.lower() for k in ("radio", "musik", "music", "bot", "chat", "allgemein", "general"))), None)
                return preferred or text_channels[0]

        # 2. No category — return first sendable text channel in guild
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                return c

    # 3. System channel
    if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
        return guild.system_channel

    # 4. ALERT_CHANNEL_ID fallback
    if ALERT_CHANNEL_ID:
        ch = guild.get_channel(ALERT_CHANNEL_ID)
        if isinstance(ch, discord.TextChannel) and ch.permissions_for(guild.me).send_messages:
            return ch

    # 5. First sendable text channel
    for c in guild.text_channels:
        if c.permissions_for(guild.me).send_messages:
            return c

    return None


async def _post_alert_to_discord(alert: dict) -> None:
    """Post a new dashboard/alert message into every guild the bot is active in."""
    sender  = alert.get("senderId") or alert.get("clientId") or "Dashboard"
    message = alert.get("message", "")
    if not message:
        return

    e = discord.Embed(
        title="📡 Nachricht vom Dashboard",
        description=message,
        color=EMBED_COLOR,
    )
    e.set_footer(text=f"Von: {sender} · 666SOUNDsDESIGn Dashboard")

    for guild in bot.guilds:
        channel = _find_best_text_channel(guild)
        if not channel:
            log.debug("Kein geeigneter Text-Channel in Guild %s gefunden", guild.name)
            continue
        try:
            await channel.send(embed=e)
            log.info("Dashboard-Alert in #%s (%s) gepostet", channel.name, guild.name)
        except Exception as exc:
            log.warning("Alert posten fehlgeschlagen (%s / #%s): %s", guild.name, channel.name, exc)


@bot.event
async def on_ready_messenger():
    """Background task started from on_ready to poll the alert relay."""
    pass  # started in on_ready via create_task


async def _messenger_poll_loop() -> None:
    """Poll the Player Alert Relay every 15 seconds and post new messages."""
    await bot.wait_until_ready()
    if not ALERT_API_URL:
        log.info("ALERT_API_URL nicht gesetzt — Messenger-Polling deaktiviert")
        return
    log.info("Messenger-Polling gestartet → %s", ALERT_API_URL)
    while not bot.is_closed():
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"{ALERT_API_URL}/api/player-alert/history", timeout=aiohttp.ClientTimeout(total=10)) as r:
                    if r.status == 200:
                        data = await r.json()
                        items = data.get("items", [])
                        for item in reversed(items):
                            aid = item.get("id", "")
                            if not aid or aid in _alert_seen_ids:
                                continue
                            _alert_seen_ids.add(aid)
                            sender = item.get("senderId") or item.get("clientId") or ""
                            if sender.endswith("[Dashboard]") or "Dashboard" in sender:
                                await _post_alert_to_discord(item)
        except Exception as exc:
            log.debug("Messenger-Poll Fehler: %s", exc)
        await asyncio.sleep(15)


@bot.tree.command(name="message", description="Nachricht an das 666SOUNDsDESIGn Dashboard senden")
@app_commands.describe(text="Deine Nachricht (max. 200 Zeichen)")
async def cmd_message(interaction: discord.Interaction, text: str):
    if not ALERT_API_URL:
        await interaction.response.send_message("❌ ALERT_API_URL ist nicht konfiguriert.", ephemeral=True)
        return
    if len(text) > 200:
        await interaction.response.send_message("❌ Nachricht zu lang (max. 200 Zeichen).", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    sender = f"{interaction.user.display_name} [Discord]"
    payload = {
        "message": text,
        "senderId": sender,
        "clientId": interaction.user.name,
        "id": f"discord-{interaction.id}",
        "source": "discord",
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.post(
                f"{ALERT_API_URL}/api/player-alert/send",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as r:
                data = await r.json()
    except Exception as exc:
        await interaction.followup.send(f"❌ Fehler: {exc}", ephemeral=True)
        return
    if data.get("ok"):
        e = discord.Embed(
            title="📡 Nachricht gesendet",
            description=f"**{interaction.user.display_name}** → Dashboard\n\n> {text}",
            color=EMBED_COLOR,
        )
        e.set_footer(text="Erscheint im 666SOUNDsDESIGn Dashboard · Fraggle DNA")
        _alert_seen_ids.add(f"discord-{interaction.id}")
        await interaction.followup.send(embed=e)
    else:
        await interaction.followup.send("❌ Dashboard hat nicht geantwortet.", ephemeral=True)


@bot.tree.command(name="dashboard-status", description="Dashboard Messenger Status prüfen")
async def cmd_dashboard_status(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if not ALERT_API_URL:
        await interaction.followup.send("❌ ALERT_API_URL nicht konfiguriert.", ephemeral=True)
        return
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f"{ALERT_API_URL}/api/player-alert/status", timeout=aiohttp.ClientTimeout(total=8)) as r:
                data = await r.json()
        e = discord.Embed(title="📊 Dashboard Messenger Status", color=EMBED_COLOR)
        e.add_field(name="Status", value="✅ Online" if data.get("ok") else "❌ Fehler", inline=True)
        e.add_field(name="Nachrichten (History)", value=str(data.get("history_size", 0)), inline=True)
        e.add_field(name="Aktive Nachricht", value="Ja" if data.get("current_active") else "Nein", inline=True)
        e.add_field(name="TTL", value=f"{data.get('ttl_seconds', '–')}s", inline=True)
        e.set_footer(text="666SOUNDsDESIGn Player Alert Relay")
        await interaction.followup.send(embed=e, ephemeral=True)
    except Exception as exc:
        await interaction.followup.send(f"❌ Nicht erreichbar: {exc}", ephemeral=True)


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN ist nicht gesetzt!")
    if not STREAM_URL:
        log.warning("STREAM_URL nicht gesetzt — /play ohne Argument funktioniert nicht")
    bot.run(DISCORD_TOKEN)
