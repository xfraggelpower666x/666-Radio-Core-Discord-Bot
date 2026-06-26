from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import discord
from discord import app_commands
from discord.ext import commands, tasks
import psutil

from health_server import HealthServer
from alert_bridge import RadioAlertBridge
from hybrid_autodj import LocalAutoDJSubsystem
from presets import PresetRegistry
from remote_control import RemoteAutoDJController

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

# ============================================================
# 666 RadioBotAI - Discord Voice Radio Bot
# Hybridstand: v3.3.0-24x7-alert-worker-admin-bridge
# - Secrets aus .env statt config.json
# - Slash-Command-Sync repariert
# - stats-Variablen-Crash repariert
# - Admin/DJ-Rollenlogik erweitert
# - /play, /stop, /pause, /resume, /volume, /nowplaying, /status
# - FFmpeg-Reconnect-Optionen für WebRadio-Streams
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
BOTCONFIG_DIR = BASE_DIR / "botconfig"
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.FileHandler(BASE_DIR / "bot.log", encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger("666RadioBotAI")


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=4, ensure_ascii=False)
    tmp_path.replace(path)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


def env_int(name: str, default: Optional[int] = None) -> Optional[int]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        logger.warning("Ungültiger Integer in %s: %r", name, value)
        return default


def env_int_list(name: str) -> list[int]:
    value = os.getenv(name, "")
    result: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            logger.warning("Ungültige Channel-ID in %s: %r", name, part)
    return result


config = read_json(BOTCONFIG_DIR / "config.json", {})
TOKEN = os.getenv("DISCORD_TOKEN") or config.get("token", "")
PREFIX = os.getenv("COMMAND_PREFIX") or config.get("prefix", "!")
OWNER_ID = env_int("DISCORD_OWNER_ID") or env_int("OWNER_ID") or int(config.get("ownerid") or 0)
GUILD_ID = env_int("DISCORD_GUILD_ID")
DEFAULT_TEXT_CHANNEL_ID = env_int("RADIO_TEXT_CHANNEL_ID")
DEFAULT_VOICE_CHANNEL_IDS = env_int_list("RADIO_VOICE_CHANNEL_ID")
DEFAULT_STREAM_URL = os.getenv("RADIO_STREAM_URL", "").strip()
DEFAULT_STREAM_NAME = os.getenv("RADIO_STREAM_NAME", "666SOUNDsDESIGn WebRadio").strip()
AUTO_JOIN_ON_READY = env_bool("AUTO_JOIN_ON_READY", False)
GLOBAL_AUTO_RECONNECT = env_bool("AUTO_RECONNECT", True)
GLOBAL_DISCONNECT_WHEN_ALONE = env_bool("DISCONNECT_WHEN_ALONE", False)
DEFAULT_VOLUME = max(0, min(env_int("DEFAULT_VOLUME", 70) or 70, 200)) / 100
INVITE_WITH_ADMIN = env_bool("INVITE_WITH_ADMIN", True)
ENV_DJ_ROLE_ID = env_int("DJ_ROLE_ID")
WEBSITE_HOME_URL = os.getenv("WEBSITE_HOME_URL", "https://webradio.666soundsdesign-broadcaster.com/").strip()
WORKER_BASE_URL = os.getenv("RADIOBOTAI_WORKER_URL", "https://666radiobotai.666soundsdesign-broadcaster.com").strip().rstrip("/")
WORKER_DASHBOARD_URL = os.getenv("RADIOBOTAI_DASHBOARD_URL", f"{WORKER_BASE_URL}/dashboard").strip()

PRESETS = PresetRegistry()
REMOTE_SKIP = RemoteAutoDJController()
RADIO_ALERT = RadioAlertBridge()

radio_urls: Dict[str, str] = read_json(BOTCONFIG_DIR / "radiostation.json", {})
radio_names_raw = read_json(BOTCONFIG_DIR / "radioid.json", {})
radio_name_to_id = radio_names_raw.get("radioid", {}) if isinstance(radio_names_raw, dict) else {}
radio_id_to_name = {str(v): str(k) for k, v in radio_name_to_id.items()}

# Die fünf Presets sind die kanonische Stream-/AutoDJ-Auswahl.
for _preset in PRESETS.audio_presets():
    radio_urls.setdefault(_preset.preset_id, _preset.url)
    radio_id_to_name.setdefault(_preset.preset_id, _preset.name)

if DEFAULT_STREAM_URL:
    radio_urls.setdefault("default", DEFAULT_STREAM_URL)
    radio_id_to_name.setdefault("default", DEFAULT_STREAM_NAME)

stats_data = read_json(
    DB_DIR / "stats.json",
    {"commands_used": 0, "errors": 0, "start_time": time.time(), "last_error": None},
)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
ready_once = False

# guild_id -> station info
current_stations: Dict[int, Dict[str, Any]] = {}
guild_modes: Dict[int, str] = {}
mode_locks: Dict[int, asyncio.Lock] = {}
local_autodj: Optional[LocalAutoDJSubsystem] = None
health_server: Optional[HealthServer] = None

FFMPEG_BEFORE_OPTIONS = (
    "-reconnect 1 "
    "-reconnect_streamed 1 "
    "-reconnect_delay_max 5 "
    "-nostdin"
)
FFMPEG_OPTIONS = "-vn -loglevel warning"


def save_stats() -> None:
    write_json(DB_DIR / "stats.json", stats_data)


def bump_command(command_name: str) -> None:
    stats_data["commands_used"] = int(stats_data.get("commands_used", 0)) + 1
    stats_data["last_command"] = command_name
    stats_data["last_command_at"] = datetime.utcnow().isoformat()
    save_stats()


def bump_error(error: Exception | str) -> None:
    stats_data["errors"] = int(stats_data.get("errors", 0)) + 1
    stats_data["last_error"] = str(error)
    stats_data["last_error_at"] = datetime.utcnow().isoformat()
    save_stats()


def guild_config_path(guild_id: int) -> Path:
    return DB_DIR / f"guild_{guild_id}.json"


def legacy_role_config() -> Dict[str, Any]:
    return read_json(DB_DIR / "role.json", {})


def get_guild_config(guild_id: int) -> Dict[str, Any]:
    legacy = legacy_role_config()
    data = read_json(guild_config_path(guild_id), {})
    return {
        "dj_role_id": data.get("dj_role_id") or legacy.get("role") or ENV_DJ_ROLE_ID,
        "auto_reconnect": data.get("auto_reconnect", GLOBAL_AUTO_RECONNECT),
        "disconnect_when_alone": data.get("disconnect_when_alone", GLOBAL_DISCONNECT_WHEN_ALONE),
        "now_playing_channel": data.get("now_playing_channel") or DEFAULT_TEXT_CHANNEL_ID,
        "default_voice_channel_ids": data.get("default_voice_channel_ids") or DEFAULT_VOICE_CHANNEL_IDS,
        "volume": float(data.get("volume", DEFAULT_VOLUME)),
        "current_station": data.get("current_station", "default" if DEFAULT_STREAM_URL else None),
    }


def save_guild_config(guild_id: int, data: Dict[str, Any]) -> None:
    current = get_guild_config(guild_id)
    current.update(data)
    write_json(guild_config_path(guild_id), current)


def station_label(station_id: str) -> str:
    return radio_id_to_name.get(str(station_id), f"Radio Station {station_id}")


def first_station_id() -> Optional[str]:
    if "default" in radio_urls:
        return "default"
    if radio_urls:
        return sorted(radio_urls.keys(), key=str)[0]
    return None


def get_station(station_id: Optional[str]) -> Tuple[str, str, str]:
    chosen = str(station_id or "").strip() or first_station_id()
    if not chosen or chosen not in radio_urls:
        raise ValueError("Keine gültige Radio-Station gefunden. Prüfe RADIO_STREAM_URL oder botconfig/radiostation.json.")
    return chosen, station_label(chosen), radio_urls[chosen]


def current_mode(guild_id: int) -> str:
    return guild_modes.get(guild_id, "stream" if guild_id in current_stations else "idle")


def mode_lock(guild_id: int) -> asyncio.Lock:
    lock = mode_locks.get(guild_id)
    if lock is None:
        lock = asyncio.Lock()
        mode_locks[guild_id] = lock
    return lock


async def prepare_stream_mode(guild: discord.Guild) -> None:
    global local_autodj
    if local_autodj and local_autodj.available:
        await local_autodj.deactivate(keep_voice=True)
    guild_modes[guild.id] = "stream"


async def activate_local_mode(guild: discord.Guild, channel: discord.VoiceChannel) -> None:
    global local_autodj
    async with mode_lock(guild.id):
        if not local_autodj or not local_autodj.available:
            raise RuntimeError("Lokaler AutoDJ ist nicht aktiviert oder DISCORD_GUILD_ID fehlt.")
        voice = guild.voice_client
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()
        current_stations.pop(guild.id, None)
        guild_modes[guild.id] = "local_autodj"
        await local_autodj.activate(guild, channel)


def hybrid_status_payload() -> Dict[str, Any]:
    return {
        "ok": True,
        "service": "666SOUNDsDESIGn RadioBotAI Hybrid",
        "version": "v3.3.0",
        "discord_ready": bot.is_ready(),
        "discord_user": str(bot.user) if bot.user else None,
        "guilds": len(bot.guilds),
        "voice_connections": sum(1 for guild in bot.guilds if guild.voice_client),
        "modes": {str(guild_id): mode for guild_id, mode in guild_modes.items()},
        "remote_skip": REMOTE_SKIP.masked_summary(),
        "radio_alert": RADIO_ALERT.masked_summary(),
        "local_autodj": local_autodj.status() if local_autodj else {"enabled": False},
        "website": WEBSITE_HOME_URL,
        "worker": WORKER_BASE_URL,
    }


def create_audio_source(url: str, volume: float) -> discord.PCMVolumeTransformer:
    source = discord.FFmpegPCMAudio(url, before_options=FFMPEG_BEFORE_OPTIONS, options=FFMPEG_OPTIONS)
    return discord.PCMVolumeTransformer(source, volume=max(0.0, min(volume, 2.0)))


def user_is_owner(user: discord.abc.User) -> bool:
    return bool(OWNER_ID and user.id == OWNER_ID)


def interaction_is_controller(interaction: discord.Interaction) -> bool:
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        return False
    if user_is_owner(interaction.user):
        return True
    if interaction.user.guild_permissions.administrator:
        return True
    cfg = get_guild_config(interaction.guild.id)
    role_id = cfg.get("dj_role_id")
    if role_id:
        role = interaction.guild.get_role(int(role_id))
        if role and role in interaction.user.roles:
            return True
    return False


def ctx_is_controller(ctx: commands.Context) -> bool:
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        return False
    if user_is_owner(ctx.author):
        return True
    if ctx.author.guild_permissions.administrator:
        return True
    cfg = get_guild_config(ctx.guild.id)
    role_id = cfg.get("dj_role_id")
    if role_id:
        role = ctx.guild.get_role(int(role_id))
        if role and role in ctx.author.roles:
            return True
    return False


async def require_interaction_controller(interaction: discord.Interaction) -> bool:
    if interaction_is_controller(interaction):
        return True
    await interaction.response.send_message(
        "❌ Du brauchst Administrator-Rechte, die DJ-Rolle oder Owner-Rechte für diesen Befehl.",
        ephemeral=True,
    )
    return False


def controller_check():
    async def predicate(ctx: commands.Context) -> bool:
        if ctx_is_controller(ctx):
            return True
        raise commands.CheckFailure("Keine DJ-/Admin-Berechtigung")

    return commands.check(predicate)


async def pick_voice_channel(
    guild: discord.Guild,
    user: discord.abc.User,
    explicit_channel: Optional[discord.VoiceChannel],
) -> discord.VoiceChannel:
    if explicit_channel:
        return explicit_channel

    if isinstance(user, discord.Member) and user.voice and user.voice.channel:
        return user.voice.channel

    cfg = get_guild_config(guild.id)
    for channel_id in cfg.get("default_voice_channel_ids", []):
        channel = guild.get_channel(int(channel_id))
        if isinstance(channel, discord.VoiceChannel):
            return channel

    raise ValueError("Kein Voice-Channel gefunden. Geh in einen Voice-Channel, nutze /play channel:#channel oder setze RADIO_VOICE_CHANNEL_ID.")


async def connect_or_move(channel: discord.VoiceChannel) -> discord.VoiceClient:
    voice_client = channel.guild.voice_client
    if voice_client and voice_client.is_connected():
        if voice_client.channel.id != channel.id:
            await voice_client.move_to(channel)
        return voice_client
    return await channel.connect(timeout=20, reconnect=True)


async def play_station(
    guild: discord.Guild,
    channel: discord.VoiceChannel,
    station_id: Optional[str],
) -> Dict[str, Any]:
    await prepare_stream_mode(guild)
    chosen_id, name, url = get_station(station_id)
    cfg = get_guild_config(guild.id)
    volume = float(cfg.get("volume", DEFAULT_VOLUME))
    voice_client = await connect_or_move(channel)

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    source = create_audio_source(url, volume)

    def after_playback(error: Optional[Exception]) -> None:
        if error:
            logger.error("Playback-Fehler in Guild %s: %s", guild.id, error)
            bump_error(error)
        bot.loop.call_soon_threadsafe(lambda: asyncio.create_task(handle_playback_end(guild.id)))

    voice_client.play(source, after=after_playback)
    station_info = {
        "station_id": chosen_id,
        "name": name,
        "url": url,
        "channel_id": channel.id,
        "started_at": time.time(),
        "volume": volume,
    }
    current_stations[guild.id] = station_info
    save_guild_config(guild.id, {"current_station": chosen_id, "volume": volume})
    return station_info


async def handle_playback_end(guild_id: int) -> None:
    await asyncio.sleep(3)
    station_info = current_stations.get(guild_id)
    if not station_info:
        return
    guild = bot.get_guild(guild_id)
    if not guild:
        return
    cfg = get_guild_config(guild_id)
    if not cfg.get("auto_reconnect", GLOBAL_AUTO_RECONNECT):
        return
    voice_client = guild.voice_client
    if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
        return
    channel = guild.get_channel(int(station_info["channel_id"]))
    if isinstance(channel, discord.VoiceChannel):
        try:
            await play_station(guild, channel, station_info.get("station_id"))
            logger.info("Auto-Reconnect: Stream in %s neu gestartet", guild.name)
        except Exception as exc:
            logger.error("Auto-Reconnect fehlgeschlagen in %s: %s", guild.name, exc)
            bump_error(exc)


# Registrierung der zweiten Engine erfolgt vor dem Discord-Command-Sync.
local_autodj = LocalAutoDJSubsystem(bot, activate_local_mode)
health_server = HealthServer(hybrid_status_payload)


def build_nowplaying_embed(guild: discord.Guild) -> discord.Embed:
    station = current_stations.get(guild.id)
    voice = guild.voice_client
    cfg = get_guild_config(guild.id)
    mode = current_mode(guild.id)
    title = "🎵 666 RadioBotAI - Now Playing" if station else "📻 666 RadioBotAI - Status"
    embed = discord.Embed(title=title, color=discord.Color.magenta(), timestamp=datetime.utcnow())
    if station:
        uptime = str(timedelta(seconds=int(time.time() - station.get("started_at", time.time()))))
        embed.add_field(name="Station", value=station.get("name", "Unbekannt"), inline=True)
        embed.add_field(name="Voice", value=voice.channel.mention if voice and voice.channel else "Nicht verbunden", inline=True)
        embed.add_field(name="Laufzeit", value=uptime, inline=True)
        embed.add_field(name="Volume", value=f"{int(float(station.get('volume', cfg.get('volume', DEFAULT_VOLUME))) * 100)}%", inline=True)
        embed.add_field(name="Auto-Reconnect", value="ON" if cfg.get("auto_reconnect") else "OFF", inline=True)
    else:
        if mode == "local_autodj" and local_autodj and local_autodj.radio:
            song = local_autodj.radio.current_song or {}
            embed.description = "Lokaler AutoDJ ist aktiv."
            if song:
                embed.add_field(name="Track", value=f"{song.get('artist', 'Unknown')} - {song.get('title', 'Unknown')}", inline=False)
        else:
            embed.description = "Aktuell läuft kein Stream."
    embed.add_field(name="Modus", value=mode, inline=True)
    return embed


class MusicControlView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    async def allowed(self, interaction: discord.Interaction) -> bool:
        if interaction_is_controller(interaction):
            return True
        await interaction.response.send_message("❌ Keine DJ-/Admin-Berechtigung.", ephemeral=True)
        return False

    @discord.ui.button(label="Pause", emoji="⏸️", style=discord.ButtonStyle.secondary, custom_id="radio_pause")
    async def pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.allowed(interaction):
            return
        vc = interaction.guild.voice_client if interaction.guild else None
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Stream pausiert.", ephemeral=True)
        elif vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Stream fortgesetzt.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Es läuft kein Stream.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="radio_stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.allowed(interaction):
            return
        if interaction.guild and interaction.guild.voice_client:
            interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect(force=True)
            current_stations.pop(interaction.guild.id, None)
            await interaction.response.send_message("⏹️ Stream gestoppt und Voice getrennt.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Bot ist nicht verbunden.", ephemeral=True)

    @discord.ui.button(label="Reconnect", emoji="🔄", style=discord.ButtonStyle.primary, custom_id="radio_reconnect")
    async def reconnect_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.allowed(interaction):
            return
        if not interaction.guild:
            await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
            return
        station = current_stations.get(interaction.guild.id)
        if not station:
            await interaction.response.send_message("❌ Kein letzter Stream gespeichert.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(int(station["channel_id"]))
        if not isinstance(channel, discord.VoiceChannel):
            await interaction.response.send_message("❌ Letzter Voice-Channel wurde nicht gefunden.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await play_station(interaction.guild, channel, station.get("station_id"))
        await interaction.followup.send("🔄 Stream neu verbunden.", ephemeral=True)


@bot.event
async def on_ready():
    global ready_once
    logger.info("Eingeloggt als %s (%s)", bot.user, bot.user.id if bot.user else "unknown")
    print(f"🎵 666 RadioBotAI online: {bot.user}")

    if ready_once:
        return
    ready_once = True

    bot.add_view(MusicControlView(0))

    try:
        if local_autodj and local_autodj.available:
            await local_autodj.initialize()
    except Exception as exc:
        logger.error("Lokaler AutoDJ konnte nicht initialisiert werden: %s", exc)
        bump_error(exc)

    try:
        if health_server:
            await health_server.start()
    except Exception as exc:
        logger.error("Healthserver konnte nicht gestartet werden: %s", exc)
        bump_error(exc)

    try:
        if GUILD_ID:
            guild_obj = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild_obj)
            synced = await bot.tree.sync(guild=guild_obj)
            logger.info("Slash-Commands für Guild %s synchronisiert: %s", GUILD_ID, len(synced))
        else:
            synced = await bot.tree.sync()
            logger.info("Globale Slash-Commands synchronisiert: %s", len(synced))
    except Exception as exc:
        logger.error("Slash-Command-Sync fehlgeschlagen: %s", exc)
        bump_error(exc)

    safe_start_task(update_activity)
    safe_start_task(check_voice_connections)
    safe_start_task(check_empty_voice_channels)

    if AUTO_JOIN_ON_READY:
        await auto_join_defaults()

    await send_restart_notice()


def safe_start_task(task_loop: tasks.Loop) -> None:
    if not task_loop.is_running():
        task_loop.start()


async def send_restart_notice() -> None:
    restart_path = DB_DIR / "restart_data.json"
    data = read_json(restart_path, None)
    if not data:
        return
    channel = bot.get_channel(int(data.get("channel_id", 0)))
    if channel and isinstance(channel, discord.abc.Messageable):
        try:
            await channel.send("✅ 666 RadioBotAI wurde neu gestartet und ist wieder online.")
        except Exception as exc:
            logger.warning("Restart-Hinweis konnte nicht gesendet werden: %s", exc)
    try:
        restart_path.unlink(missing_ok=True)
    except Exception:
        pass


async def auto_join_defaults() -> None:
    for guild in bot.guilds:
        cfg = get_guild_config(guild.id)
        station_id = cfg.get("current_station") or first_station_id()
        for channel_id in cfg.get("default_voice_channel_ids", []):
            channel = guild.get_channel(int(channel_id))
            if isinstance(channel, discord.VoiceChannel):
                try:
                    await play_station(guild, channel, station_id)
                    logger.info("Auto-Join aktiv: %s -> %s", guild.name, channel.name)
                    break
                except Exception as exc:
                    logger.error("Auto-Join fehlgeschlagen in %s: %s", guild.name, exc)
                    bump_error(exc)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if local_autodj:
        await local_autodj.on_voice_state_update(member, before, after)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    await bot.process_commands(message)


@tasks.loop(seconds=30)
async def update_activity():
    active = len([g for g in bot.guilds if g.voice_client])
    activity = f"666SOUNDsDESIGn WebRadio | {active} Voice Stream(s)"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=activity))


@tasks.loop(minutes=1)
async def check_voice_connections():
    for guild_id, station in list(current_stations.items()):
        guild = bot.get_guild(guild_id)
        if not guild:
            continue
        cfg = get_guild_config(guild_id)
        if not cfg.get("auto_reconnect", GLOBAL_AUTO_RECONNECT):
            continue
        vc = guild.voice_client
        if vc and vc.is_connected() and (vc.is_playing() or vc.is_paused()):
            continue
        channel = guild.get_channel(int(station.get("channel_id", 0)))
        if isinstance(channel, discord.VoiceChannel):
            try:
                await play_station(guild, channel, station.get("station_id"))
            except Exception as exc:
                logger.error("Watchdog-Reconnect fehlgeschlagen in %s: %s", guild.name, exc)
                bump_error(exc)


@tasks.loop(minutes=1)
async def check_empty_voice_channels():
    for guild in bot.guilds:
        vc = guild.voice_client
        if not vc or not vc.channel:
            continue
        cfg = get_guild_config(guild.id)
        if not cfg.get("disconnect_when_alone", GLOBAL_DISCONNECT_WHEN_ALONE):
            continue
        humans = [m for m in vc.channel.members if not m.bot]
        if humans:
            continue
        await asyncio.sleep(30)
        humans = [m for m in vc.channel.members if not m.bot]
        if not humans and guild.voice_client:
            guild.voice_client.stop()
            await guild.voice_client.disconnect(force=True)
            current_stations.pop(guild.id, None)
            logger.info("Auto-Disconnect in %s: Voice leer", guild.name)


async def handle_play_interaction(
    interaction: discord.Interaction,
    channel: Optional[discord.VoiceChannel] = None,
    station_id: Optional[str] = None,
    command_name: str = "play",
):
    if not await require_interaction_controller(interaction):
        return
    if not interaction.guild:
        await interaction.response.send_message("❌ /play funktioniert nur auf einem Discord-Server.", ephemeral=True)
        return
    await interaction.response.defer(thinking=True)
    try:
        voice_channel = await pick_voice_channel(interaction.guild, interaction.user, channel)
        await play_station(interaction.guild, voice_channel, station_id)
        embed = build_nowplaying_embed(interaction.guild)
        embed.description = f"✅ Stream gestartet in {voice_channel.mention}."
        await interaction.followup.send(embed=embed, view=MusicControlView(interaction.guild.id))
        bump_command(command_name)
    except Exception as exc:
        bump_error(exc)
        await interaction.followup.send(f"❌ Play fehlgeschlagen: `{exc}`", ephemeral=True)


@bot.tree.command(name="play", description="Startet den WebRadio-Stream im Voice-Channel")
@app_commands.describe(channel="Voice-Channel; leer = dein aktueller/default Channel", station_id="Station-ID aus /radiolist; leer = default")
async def slash_play(
    interaction: discord.Interaction,
    channel: Optional[discord.VoiceChannel] = None,
    station_id: Optional[str] = None,
):
    await handle_play_interaction(interaction, channel, station_id, "play")


@bot.tree.command(name="radio", description="Alias für /play")
@app_commands.describe(channel="Voice-Channel; leer = dein aktueller/default Channel", station_id="Station-ID aus /radiolist; leer = default")
async def slash_radio(
    interaction: discord.Interaction,
    channel: Optional[discord.VoiceChannel] = None,
    station_id: Optional[str] = None,
):
    await handle_play_interaction(interaction, channel, station_id, "radio")


@bot.tree.command(name="stop", description="Stoppt den Stream und trennt den Bot vom Voice-Channel")
async def slash_stop(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    if interaction.guild and interaction.guild.voice_client:
        if local_autodj:
            await local_autodj.deactivate(keep_voice=True)
        interaction.guild.voice_client.stop()
        await interaction.guild.voice_client.disconnect(force=True)
        current_stations.pop(interaction.guild.id, None)
        guild_modes[interaction.guild.id] = "idle"
        await interaction.response.send_message("⏹️ Wiedergabe gestoppt und Voice getrennt.")
        bump_command("stop")
    else:
        await interaction.response.send_message("❌ Bot ist nicht mit einem Voice-Channel verbunden.", ephemeral=True)


@bot.tree.command(name="pause", description="Pausiert den laufenden Stream")
async def slash_pause(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    vc = interaction.guild.voice_client if interaction.guild else None
    if interaction.guild and current_mode(interaction.guild.id) == "local_autodj" and local_autodj:
        if await local_autodj.pause():
            await interaction.response.send_message("⏸️ Lokaler AutoDJ pausiert.")
            bump_command("pause")
            return
    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Stream pausiert.")
        bump_command("pause")
    else:
        await interaction.response.send_message("❌ Es läuft kein Stream.", ephemeral=True)


@bot.tree.command(name="resume", description="Setzt den pausierten Stream fort")
async def slash_resume(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    vc = interaction.guild.voice_client if interaction.guild else None
    if interaction.guild and current_mode(interaction.guild.id) == "local_autodj" and local_autodj:
        if await local_autodj.resume():
            await interaction.response.send_message("▶️ Lokaler AutoDJ fortgesetzt.")
            bump_command("resume")
            return
    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Stream fortgesetzt.")
        bump_command("resume")
    else:
        await interaction.response.send_message("❌ Der Stream ist nicht pausiert.", ephemeral=True)


@bot.tree.command(name="volume", description="Setzt die Bot-Lautstärke von 0 bis 200 Prozent")
@app_commands.describe(level="0 bis 200 Prozent")
async def slash_volume(interaction: discord.Interaction, level: app_commands.Range[int, 0, 200]):
    if not await require_interaction_controller(interaction):
        return
    if not interaction.guild:
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    volume = int(level) / 100
    save_guild_config(interaction.guild.id, {"volume": volume})
    station = current_stations.get(interaction.guild.id)
    vc = interaction.guild.voice_client
    if station:
        station["volume"] = volume
    if interaction.guild and current_mode(interaction.guild.id) == "local_autodj" and local_autodj:
        await local_autodj.set_volume(volume)
    elif vc and isinstance(vc.source, discord.PCMVolumeTransformer):
        vc.source.volume = volume
    await interaction.response.send_message(f"🔊 Lautstärke gesetzt: **{level}%**")
    bump_command("volume")


@bot.tree.command(name="nowplaying", description="Zeigt den aktuellen Streamstatus")
async def slash_nowplaying(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    await interaction.response.send_message(embed=build_nowplaying_embed(interaction.guild))
    bump_command("nowplaying")


@bot.tree.command(name="status", description="Zeigt Bot-, Voice- und Systemstatus")
async def slash_status(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    process = psutil.Process(os.getpid())
    uptime = str(timedelta(seconds=int(time.time() - stats_data.get("start_time", time.time()))))
    embed = build_nowplaying_embed(interaction.guild)
    embed.title = "📊 666 RadioBotAI - Status"
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)} ms", inline=True)
    embed.add_field(name="Uptime", value=uptime, inline=True)
    embed.add_field(name="RAM", value=f"{process.memory_info().rss / 1024 / 1024:.1f} MB", inline=True)
    embed.add_field(name="Commands", value=str(stats_data.get("commands_used", 0)), inline=True)
    embed.add_field(name="Errors", value=str(stats_data.get("errors", 0)), inline=True)
    embed.add_field(name="Worker Skip", value=REMOTE_SKIP.masked_summary(), inline=False)
    embed.add_field(name="24/7 Health", value=f"Port {health_server.port if health_server else 'aus'}", inline=True)
    await interaction.response.send_message(embed=embed)
    bump_command("status")


@bot.tree.command(name="radiolist", description="Listet verfügbare Radio-Stationen")
async def slash_radiolist(interaction: discord.Interaction):
    lines = []
    for key in sorted(radio_urls.keys(), key=str):
        url = radio_urls[key]
        safe_url = url if len(url) < 80 else url[:77] + "..."
        lines.append(f"{key}: {station_label(key)} -> {safe_url}")
    if not lines:
        lines.append("Keine Stationen konfiguriert. Setze RADIO_STREAM_URL oder botconfig/radiostation.json.")
    embed = discord.Embed(
        title="📻 Radio Stations",
        description="```text\n" + "\n".join(lines[:30]) + "\n```",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    bump_command("radiolist")


@bot.tree.command(name="presets", description="Zeigt die fünf 666SOUNDsDESIGn Stream-Presets")
async def slash_presets(interaction: discord.Interaction):
    lines = []
    for preset in PRESETS.all():
        marker = "▶" if preset.playable else ("🎛" if preset.type == "local_autodj" else "🔗")
        lines.append(f"**{preset.preset_id}. {preset.name}** {marker}\n{preset.description}")
    embed = discord.Embed(
        title="🎚️ 666 RadioBotAI - Stream Presets",
        description="\n\n".join(lines),
        color=discord.Color.purple(),
        timestamp=datetime.utcnow(),
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    bump_command("presets")


@bot.tree.command(name="preset", description="Aktiviert eines der fünf Stream-/AutoDJ-Presets")
@app_commands.choices(preset=[
    app_commands.Choice(name="1 - Main Stream", value="1"),
    app_commands.Choice(name="2 - SSL Port 8686", value="2"),
    app_commands.Choice(name="3 - SSL /stream", value="3"),
    app_commands.Choice(name="4 - TuneIn Player", value="4"),
    app_commands.Choice(name="5 - Local AutoDJ", value="5"),
])
@app_commands.describe(preset="Preset 1 bis 5", channel="Voice-Channel; leer = dein aktueller/default Channel")
async def slash_preset(
    interaction: discord.Interaction,
    preset: app_commands.Choice[str],
    channel: Optional[discord.VoiceChannel] = None,
):
    if not await require_interaction_controller(interaction):
        return
    if not interaction.guild:
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    selected = PRESETS.get(preset.value)
    if selected.type == "external_link":
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="TuneIn öffnen", url=selected.url))
        await interaction.response.send_message(
            f"🔗 **{selected.name}** ist ein Webplayer und wird nicht als direkter FFmpeg-Stream gestartet.",
            view=view,
            ephemeral=True,
        )
        bump_command("preset_4")
        return
    try:
        voice_channel = await pick_voice_channel(interaction.guild, interaction.user, channel)
        await interaction.response.defer(ephemeral=True)
        if selected.type == "local_autodj":
            await activate_local_mode(interaction.guild, voice_channel)
            await interaction.followup.send(
                f"🎛️ Preset 5 aktiv: **{selected.name}** in {voice_channel.mention}. Nutze `/track` für gezielte Titel.",
                ephemeral=True,
            )
        else:
            await play_station(interaction.guild, voice_channel, selected.preset_id)
            await interaction.followup.send(
                f"✅ Preset {selected.preset_id} aktiv: **{selected.name}** in {voice_channel.mention}.",
                ephemeral=True,
            )
        bump_command(f"preset_{selected.preset_id}")
    except Exception as exc:
        bump_error(exc)
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Preset konnte nicht aktiviert werden: `{exc}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Preset konnte nicht aktiviert werden: `{exc}`", ephemeral=True)


@bot.tree.command(name="autodj", description="Aktiviert direkt Preset 5: lokale AutoDJ-Musikbibliothek")
@app_commands.describe(channel="Voice-Channel; leer = dein aktueller/default Channel")
async def slash_autodj(interaction: discord.Interaction, channel: Optional[discord.VoiceChannel] = None):
    if not await require_interaction_controller(interaction):
        return
    if not interaction.guild:
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    try:
        voice_channel = await pick_voice_channel(interaction.guild, interaction.user, channel)
        await interaction.response.defer(ephemeral=True)
        await activate_local_mode(interaction.guild, voice_channel)
        await interaction.followup.send(f"🎛️ Lokaler AutoDJ aktiv in {voice_channel.mention}.", ephemeral=True)
        bump_command("autodj")
    except Exception as exc:
        bump_error(exc)
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ AutoDJ-Start fehlgeschlagen: `{exc}`", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ AutoDJ-Start fehlgeschlagen: `{exc}`", ephemeral=True)


@bot.tree.command(name="skip", description="Überspringt den aktuellen lokalen oder SHOUTcast-AutoDJ-Titel")
async def slash_skip(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    if not interaction.guild:
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    if current_mode(interaction.guild.id) == "local_autodj" and local_autodj:
        try:
            await local_autodj.skip()
            await interaction.followup.send("⏭️ Lokaler AutoDJ: nächster Titel angefordert.", ephemeral=True)
            bump_command("skip_local")
            return
        except Exception as exc:
            bump_error(exc)
            await interaction.followup.send(f"❌ Lokaler Skip fehlgeschlagen: `{exc}`", ephemeral=True)
            return
    result = await REMOTE_SKIP.skip()
    await interaction.followup.send(("⏭️ " if result.ok else "❌ ") + result.message, ephemeral=True)
    if result.ok:
        bump_command("skip_remote")
    else:
        bump_error(result.message)


@bot.tree.command(name="skipstatus", description="Prüft die geschützte AutoDJ-/skip-Worker-Verbindung")
async def slash_skipstatus(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    await interaction.response.defer(ephemeral=True)
    status = await REMOTE_SKIP.status()
    embed = discord.Embed(
        title="🔐 AutoDJ Skip Bridge",
        color=discord.Color.green() if status.get("reachable") else discord.Color.orange(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Modus", value=str(status.get("mode", "unknown")), inline=True)
    embed.add_field(name="Geschützt", value="JA" if status.get("protected") else "NEIN", inline=True)
    embed.add_field(name="Erreichbar", value="JA" if status.get("reachable") else "NEIN/UNGEPRÜFT", inline=True)
    embed.add_field(name="Route", value=str(status.get("target", "nicht gesetzt")), inline=False)
    embed.add_field(name="Direkter Admin-Fallback", value="ON" if status.get("direct_admin_fallback") else "OFF", inline=True)
    embed.add_field(name="HTTP", value=str(status.get("http_status") or "-") , inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)
    bump_command("skipstatus")


@bot.tree.command(name="radioalert", description="Postet eine geschützte Nachricht an den WebRadio Player-Alert-Service")
@app_commands.describe(message="Nachricht für den WebRadio-Player, maximal 240 Zeichen")
async def slash_radioalert(interaction: discord.Interaction, message: str):
    if not await require_interaction_controller(interaction):
        return
    await interaction.response.defer(ephemeral=True)
    metadata = {
        "guildId": str(interaction.guild.id) if interaction.guild else None,
        "channelId": str(interaction.channel_id) if interaction.channel_id else None,
        "discordUserId": str(interaction.user.id),
    }
    result = await RADIO_ALERT.send(
        message,
        sender_id=str(interaction.user.id),
        source="666radiobotai-discord-hybrid",
        metadata=metadata,
    )
    await interaction.followup.send(("📣 " if result.ok else "❌ ") + result.message, ephemeral=True)
    if result.ok:
        bump_command("radioalert")
    else:
        bump_error(result.message)


@bot.tree.command(name="alertstatus", description="Prüft Worker, Render-Backend und Player-Alert-Verbindung")
async def slash_alertstatus(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    await interaction.response.defer(ephemeral=True)
    status = await RADIO_ALERT.status()
    reachable = bool(status.get("worker_reachable"))
    render_data = status.get("render") if isinstance(status.get("render"), dict) else {}
    embed = discord.Embed(
        title="📣 WebRadio Player-Alert Bridge",
        color=discord.Color.green() if reachable else discord.Color.orange(),
        timestamp=datetime.utcnow(),
    )
    embed.add_field(name="Worker", value="ONLINE" if reachable else "OFFLINE/UNGEPRÜFT", inline=True)
    embed.add_field(name="Geschützt", value="JA" if status.get("protected") else "NEIN", inline=True)
    embed.add_field(name="HTTP", value=str(status.get("worker_http_status") or "-"), inline=True)
    embed.add_field(name="Route", value=str(status.get("route", "nicht gesetzt")), inline=False)
    embed.add_field(
        name="Render Backend",
        value=(
            "ONLINE" if render_data.get("backendHealthOk")
            else "KONFIGURIERT" if render_data.get("renderBackendConfigured")
            else "NICHT BESTÄTIGT"
        ),
        inline=True,
    )
    embed.add_field(name="KV Fallback", value="JA" if render_data.get("kvConfigured") else "NEIN/UNBEKANNT", inline=True)
    embed.add_field(name="Direkter Fallback", value="ON" if status.get("direct_fallback") else "OFF", inline=True)
    await interaction.followup.send(embed=embed, ephemeral=True)
    bump_command("alertstatus")


@bot.tree.command(name="alertcurrent", description="Zeigt die aktuell gespeicherte WebRadio-Player-Nachricht")
async def slash_alertcurrent(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    await interaction.response.defer(ephemeral=True)
    result = await RADIO_ALERT.current()
    data = json.dumps(result.data, indent=2, ensure_ascii=False)[:1800] if result.data is not None else result.message
    await interaction.followup.send("```json\n" + data + "\n```", ephemeral=True)
    bump_command("alertcurrent")


@bot.tree.command(name="alerthistory", description="Zeigt die letzten WebRadio-Player-Alerts")
async def slash_alerthistory(interaction: discord.Interaction):
    if not await require_interaction_controller(interaction):
        return
    await interaction.response.defer(ephemeral=True)
    result = await RADIO_ALERT.history()
    data = json.dumps(result.data, indent=2, ensure_ascii=False)[:1800] if result.data is not None else result.message
    await interaction.followup.send("```json\n" + data + "\n```", ephemeral=True)
    bump_command("alerthistory")


@bot.tree.command(name="home", description="Öffnet die 666SOUNDsDESIGn WebRadio-Webseite und das RadioBotAI-Dashboard")
async def slash_home(interaction: discord.Interaction):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="WebRadio Home", url=WEBSITE_HOME_URL))
    view.add_item(discord.ui.Button(label="RadioBotAI Dashboard", url=WORKER_DASHBOARD_URL))
    embed = discord.Embed(
        title="🏠 666SOUNDsDESIGn WebRadio",
        description=f"**Webseite:** {WEBSITE_HOME_URL}\n**RadioBotAI:** {WORKER_BASE_URL}",
        color=discord.Color.magenta(),
        timestamp=datetime.utcnow(),
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    bump_command("home")


@bot.tree.command(name="setrole", description="Setzt die DJ-/Radio-Control-Rolle")
@app_commands.describe(role="Rolle, die den Bot steuern darf")
async def slash_setrole(interaction: discord.Interaction, role: discord.Role):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    if not (user_is_owner(interaction.user) or interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ Nur Owner oder Server-Administratoren dürfen die DJ-Rolle setzen.", ephemeral=True)
        return
    save_guild_config(interaction.guild.id, {"dj_role_id": role.id})
    # Legacy-Kompatibilität für vorhandene Installationen
    write_json(DB_DIR / "role.json", {"role": role.id, "Guildid": interaction.guild.id})
    await interaction.response.send_message(f"✅ DJ-/Radio-Control-Rolle gesetzt: {role.mention}")
    bump_command("setrole")


@bot.tree.command(name="setup", description="Admin-Setup für 666 RadioBotAI")
@app_commands.describe(
    dj_role="Optional: vorhandene DJ-/Radio-Control-Rolle",
    voice_channel="Optional: Standard-Voice-Channel",
    text_channel="Optional: Status-/NowPlaying-Textkanal",
)
async def slash_setup(
    interaction: discord.Interaction,
    dj_role: Optional[discord.Role] = None,
    voice_channel: Optional[discord.VoiceChannel] = None,
    text_channel: Optional[discord.TextChannel] = None,
):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    if not (user_is_owner(interaction.user) or interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ Setup braucht Server-Administrator-Rechte.", ephemeral=True)
        return

    update: Dict[str, Any] = {}
    if dj_role:
        update["dj_role_id"] = dj_role.id
    if voice_channel:
        update["default_voice_channel_ids"] = [voice_channel.id]
    if text_channel:
        update["now_playing_channel"] = text_channel.id
    if update:
        save_guild_config(interaction.guild.id, update)

    cfg = get_guild_config(interaction.guild.id)
    role_value = f"<@&{cfg['dj_role_id']}>" if cfg.get("dj_role_id") else "nicht gesetzt"
    voice_ids = cfg.get("default_voice_channel_ids", [])
    voice_value = ", ".join(f"<#${vid}>".replace("#$", "#") for vid in voice_ids) if voice_ids else "nicht gesetzt"
    text_value = f"<#{cfg['now_playing_channel']}>" if cfg.get("now_playing_channel") else "nicht gesetzt"

    embed = discord.Embed(title="🛠️ 666 RadioBotAI Setup", color=discord.Color.purple(), timestamp=datetime.utcnow())
    embed.add_field(name="DJ-/Control-Rolle", value=role_value, inline=False)
    embed.add_field(name="Default Voice", value=voice_value, inline=False)
    embed.add_field(name="Status-/NowPlaying-Kanal", value=text_value, inline=False)
    embed.add_field(name="Start", value="/play startet den Stream. /setrole setzt die Rolle. /radiolist zeigt Stationen.", inline=False)
    embed.add_field(name="Wichtig", value="Ein Bot kann pro Discord-Server nur in einem Voice-Channel gleichzeitig verbunden sein.", inline=False)
    await interaction.response.send_message(embed=embed)
    bump_command("setup")


@bot.tree.command(name="info", description="Zeigt Projektinformationen zum Bot")
async def slash_info(interaction: discord.Interaction):
    text = (
        "**BOT NAME:** 666 RadioBotAI\n"
        "**BOT-TYP:** Discord Voice Radio Bot / WebRadio Stream Player\n"
        "**PROJEKT:** 666SOUNDsDESIGn WebRadio\n\n"
        "Der Bot verbindet sich mit einem Discord-Voice-Channel und spielt den laufenden WebRadio-Stream ab. "
        "Er ist kein Chatbot, sondern Radio-Playback- und Stream-Control-Bot.\n\n"
        "**Befehle:** /play, /preset, /presets, /autodj, /track, /skip, /skipstatus, /radioalert, /alertstatus, /alertcurrent, /alerthistory, /home, /stop, /pause, /resume, /volume, /status"
    )
    embed = discord.Embed(title="ℹ️ 666 RadioBotAI", description=text, color=discord.Color.dark_magenta(), timestamp=datetime.utcnow())
    await interaction.response.send_message(embed=embed, ephemeral=True)
    bump_command("info")


@bot.tree.command(name="ping", description="Prüft die Bot-Latenz")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong: **{round(bot.latency * 1000)} ms**", ephemeral=True)
    bump_command("ping")


@bot.tree.command(name="invite", description="Erzeugt einen Invite-Link für den Bot")
async def slash_invite(interaction: discord.Interaction):
    if INVITE_WITH_ADMIN:
        permissions = discord.Permissions(administrator=True)
        perm_text = "Administrator"
    else:
        permissions = discord.Permissions(connect=True, speak=True, send_messages=True, embed_links=True, read_message_history=True, use_slash_commands=True, manage_roles=True)
        perm_text = "Connect, Speak, Send Messages, Embed Links, Slash Commands, Manage Roles"
    url = discord.utils.oauth_url(bot.user.id, permissions=permissions, scopes=("bot", "applications.commands"))
    embed = discord.Embed(title="🔗 Invite 666 RadioBotAI", color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.description = f"[Bot einladen]({url})"
    embed.add_field(name="Berechtigungen", value=perm_text, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    bump_command("invite")


@bot.tree.command(name="synccommands", description="Synchronisiert Slash-Commands neu")
async def slash_synccommands(interaction: discord.Interaction):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("❌ Nur auf Servern nutzbar.", ephemeral=True)
        return
    if not (user_is_owner(interaction.user) or interaction.user.guild_permissions.administrator):
        await interaction.response.send_message("❌ Nur Owner oder Server-Administratoren dürfen Commands synchronisieren.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    try:
        bot.tree.copy_global_to(guild=interaction.guild)
        synced = await bot.tree.sync(guild=interaction.guild)
        await interaction.followup.send(f"✅ Slash-Commands neu synchronisiert: {len(synced)}", ephemeral=True)
        bump_command("synccommands")
    except Exception as exc:
        bump_error(exc)
        await interaction.followup.send(f"❌ Sync fehlgeschlagen: `{exc}`", ephemeral=True)


@bot.command(name="help")
async def prefix_help(ctx: commands.Context):
    embed = discord.Embed(title="📻 666 RadioBotAI - Hilfe", color=discord.Color.blue(), timestamp=datetime.utcnow())
    embed.description = (
        "Slash: `/play`, `/preset`, `/presets`, `/autodj`, `/track`, `/skip`, `/skipstatus`, `/radioalert`, `/alertstatus`, `/alertcurrent`, `/alerthistory`, `/home`, `/stop`, `/pause`, `/resume`, `/volume`, `/status`\n"
        f"Prefix: `{PREFIX}play`, `{PREFIX}stop`, `{PREFIX}radiolist`, `{PREFIX}setrole`, `{PREFIX}sync`"
    )
    await ctx.reply(embed=embed)


@bot.command(name="play")
@controller_check()
async def prefix_play(ctx: commands.Context, station_id: Optional[str] = None):
    if not ctx.guild:
        return
    try:
        channel = await pick_voice_channel(ctx.guild, ctx.author, None)
        await play_station(ctx.guild, channel, station_id)
        await ctx.reply(embed=build_nowplaying_embed(ctx.guild), view=MusicControlView(ctx.guild.id))
        bump_command("prefix_play")
    except Exception as exc:
        bump_error(exc)
        await ctx.reply(f"❌ Play fehlgeschlagen: `{exc}`")


@bot.command(name="stop")
@controller_check()
async def prefix_stop(ctx: commands.Context):
    if ctx.guild and ctx.guild.voice_client:
        if local_autodj:
            await local_autodj.deactivate(keep_voice=True)
        ctx.guild.voice_client.stop()
        await ctx.guild.voice_client.disconnect(force=True)
        current_stations.pop(ctx.guild.id, None)
        guild_modes[ctx.guild.id] = "idle"
        await ctx.reply("⏹️ Wiedergabe gestoppt.")
        bump_command("prefix_stop")


@bot.command(name="radiolist")
async def prefix_radiolist(ctx: commands.Context):
    lines = [f"{key}: {station_label(key)}" for key in sorted(radio_urls.keys(), key=str)] or ["Keine Stationen konfiguriert."]
    await ctx.reply("```text\n" + "\n".join(lines) + "\n```")
    bump_command("prefix_radiolist")


@bot.command(name="setrole")
async def prefix_setrole(ctx: commands.Context, role: discord.Role):
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        return
    if not (user_is_owner(ctx.author) or ctx.author.guild_permissions.administrator):
        await ctx.reply("❌ Nur Owner oder Server-Administratoren dürfen die DJ-Rolle setzen.")
        return
    save_guild_config(ctx.guild.id, {"dj_role_id": role.id})
    write_json(DB_DIR / "role.json", {"role": role.id, "Guildid": ctx.guild.id})
    await ctx.reply(f"✅ DJ-/Radio-Control-Rolle gesetzt: {role.mention}")
    bump_command("prefix_setrole")


@bot.command(name="sync")
async def prefix_sync(ctx: commands.Context):
    if not ctx.guild or not isinstance(ctx.author, discord.Member):
        return
    if not (user_is_owner(ctx.author) or ctx.author.guild_permissions.administrator):
        await ctx.reply("❌ Nur Owner oder Server-Administratoren dürfen Commands synchronisieren.")
        return
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.reply(f"✅ Slash-Commands synchronisiert: {len(synced)}")
        bump_command("prefix_sync")
    except Exception as exc:
        bump_error(exc)
        await ctx.reply(f"❌ Sync fehlgeschlagen: `{exc}`")


@bot.command(name="skipstatus")
@controller_check()
async def prefix_skipstatus(ctx: commands.Context):
    status = await REMOTE_SKIP.status()
    await ctx.reply(
        "```json\n" + json.dumps(status, indent=2, ensure_ascii=False)[:1800] + "\n```"
    )
    bump_command("prefix_skipstatus")


@bot.command(name="radioalert")
@controller_check()
async def prefix_radioalert(ctx: commands.Context, *, message: str):
    result = await RADIO_ALERT.send(
        message,
        sender_id=str(ctx.author.id),
        source="666radiobotai-discord-prefix",
        metadata={
            "guildId": str(ctx.guild.id) if ctx.guild else None,
            "channelId": str(ctx.channel.id),
            "discordUserId": str(ctx.author.id),
        },
    )
    await ctx.reply(("📣 " if result.ok else "❌ ") + result.message)
    if result.ok:
        bump_command("prefix_radioalert")
    else:
        bump_error(result.message)


@bot.command(name="alertstatus")
@controller_check()
async def prefix_alertstatus(ctx: commands.Context):
    status = await RADIO_ALERT.status()
    await ctx.reply("```json\n" + json.dumps(status, indent=2, ensure_ascii=False)[:1800] + "\n```")
    bump_command("prefix_alertstatus")


@bot.command(name="home")
async def prefix_home(ctx: commands.Context):
    await ctx.reply(f"🏠 {WEBSITE_HOME_URL}\n🎛️ {WORKER_DASHBOARD_URL}")
    bump_command("prefix_home")


@bot.command(name="skip")
@controller_check()
async def prefix_skip(ctx: commands.Context):
    if not ctx.guild:
        return
    if current_mode(ctx.guild.id) == "local_autodj" and local_autodj:
        await local_autodj.skip()
        await ctx.reply("⏭️ Lokaler AutoDJ: nächster Titel angefordert.")
        bump_command("prefix_skip_local")
        return
    result = await REMOTE_SKIP.skip()
    await ctx.reply(("⏭️ " if result.ok else "❌ ") + result.message)
    if result.ok:
        bump_command("prefix_skip_remote")


@bot.command(name="preset")
@controller_check()
async def prefix_preset(ctx: commands.Context, preset_id: str):
    if not ctx.guild:
        return
    try:
        preset = PRESETS.get(preset_id)
        if preset.type == "external_link":
            await ctx.reply(f"🔗 {preset.name}: {preset.url}")
            return
        channel = await pick_voice_channel(ctx.guild, ctx.author, None)
        if preset.type == "local_autodj":
            await activate_local_mode(ctx.guild, channel)
        else:
            await play_station(ctx.guild, channel, preset.preset_id)
        await ctx.reply(f"✅ Preset {preset.preset_id} aktiv: {preset.name}")
        bump_command(f"prefix_preset_{preset.preset_id}")
    except Exception as exc:
        bump_error(exc)
        await ctx.reply(f"❌ Preset-Fehler: `{exc}`")


@bot.command(name="reset")
async def prefix_reset(ctx: commands.Context):
    if not user_is_owner(ctx.author):
        await ctx.reply("❌ Nur Bot-Owner darf den Bot neu starten.")
        return
    write_json(DB_DIR / "restart_data.json", {"channel_id": ctx.channel.id, "timestamp": time.time()})
    await ctx.reply("🔄 Bot wird beendet. Container/Service sollte ihn automatisch neu starten.")
    await bot.close()


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    bump_error(error)
    if isinstance(error, commands.CheckFailure):
        message = "❌ Keine DJ-/Admin-Berechtigung."
    elif isinstance(error, commands.MissingRequiredArgument):
        message = "❌ Pflichtargument fehlt. Nutze `!help`."
    elif isinstance(error, commands.BadArgument):
        message = "❌ Ungültiges Argument. Prüfe Channel, Rolle oder Station-ID."
    else:
        message = f"❌ Fehler: `{error}`"
    try:
        await ctx.reply(message)
    except Exception:
        pass
    logger.error("Prefix-Command-Fehler: %s", error)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    bump_error(error)
    message = str(error)
    if isinstance(error, app_commands.CommandSignatureMismatch):
        message = "Slash-Command-Signatur ist veraltet. Nutze `!sync` oder `/synccommands`, danach Discord neu öffnen."
    elif isinstance(error, app_commands.CommandNotFound):
        message = "Slash-Command nicht gefunden. Nutze `!sync` oder warte auf globalen Discord-Sync."
    elif isinstance(error, app_commands.CheckFailure):
        message = "Keine Berechtigung."
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ {message}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {message}", ephemeral=True)
    except Exception:
        pass
    logger.error("Slash-Command-Fehler: %s", error)


async def run_service() -> None:
    """Startet Health-Endpunkt und Discord-Gateway im selben Prozess.

    Der Health-Port wird vor dem Gateway-Connect geöffnet. Dadurch kann ein
    24/7-Host den Prozess bereits während Discord-Reconnects überwachen.
    """
    if health_server:
        await health_server.start()
    try:
        await bot.start(TOKEN, reconnect=True)
    finally:
        if local_autodj:
            await local_autodj.shutdown()
        if health_server:
            await health_server.stop()


if __name__ == "__main__":
    if not TOKEN:
        logger.error("DISCORD_TOKEN fehlt. Erstelle .env aus .env.example und trage den Bot-Token ein.")
        print("❌ DISCORD_TOKEN fehlt. Erstelle .env aus .env.example.")
        sys.exit(1)
    logger.info("Starte 666 RadioBotAI Hybrid v3.3.0...")
    try:
        asyncio.run(run_service())
    except KeyboardInterrupt:
        logger.info("RadioBotAI wurde kontrolliert beendet.")
