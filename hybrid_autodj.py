from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Awaitable, Callable

import discord

from autodj_commands import setup_commands as setup_autodj_commands
from config_loader import load_config
from database import DatabaseManager
from monitor import start_monitoring
from player_engine import init_player, radio_player
from radio_actions import RadioAction, RadioState as RadioStatusEnum
from radio_state import RadioState
from scanner import cleanup_database, scan_music_library
from ui import (
    FrequencyStationView,
    NowPlayingView,
    UnifiedStandbyView,
    force_new_embed,
    init_ui,
    refresh_all_uis,
    update_now_playing,
)

logger = logging.getLogger("666RadioBotAI.local_autodj")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ja"}


class LocalAutoDJSubsystem:
    """Integriert die zweite hochgeladene AutoDJ-/Musikbibliotheks-Engine.

    Die Engine benutzt denselben Discord-Client und dieselbe Voice-Verbindung wie
    der Streambot. Der zentrale Mode-Manager schaltet deshalb strikt zwischen
    ``stream`` und ``local_autodj`` um.
    """

    def __init__(
        self,
        bot: discord.Client,
        activation_callback: Callable[[discord.Guild, discord.VoiceChannel], Awaitable[None]],
    ) -> None:
        self.bot = bot
        self.enabled = _env_bool("LOCAL_AUTODJ_ENABLED", True)
        self.initialized = False
        self.monitor = None
        self.background_tasks: list[asyncio.Task] = []
        self.config = None
        self.db = None
        self.radio = None

        if not self.enabled:
            logger.info("Lokaler AutoDJ ist über LOCAL_AUTODJ_ENABLED deaktiviert.")
            return

        try:
            self.config = load_config()
            self.db = DatabaseManager(self.config.db_path)
            self.radio = RadioState(self.config, self.db)
            self.radio.mode_activation_callback = activation_callback
            self.radio.runtime_mode = "local_autodj"
            # Konfliktfreie Befehle: /track und /autodjstats.
            setup_autodj_commands(bot.tree, self.radio)
        except Exception as exc:
            self.enabled = False
            logger.exception("Lokaler AutoDJ konnte nicht vorbereitet werden: %s", exc)

    @property
    def available(self) -> bool:
        return bool(
            self.enabled
            and self.config
            and self.db
            and self.radio
            and int(getattr(self.config, "guild_id", 0) or 0) > 0
        )

    async def initialize(self) -> None:
        if self.initialized or not self.available:
            return

        await self.db.initialize()
        now = int(time.time())

        if _env_bool("LOCAL_AUTODJ_CLEANUP_ON_START", True):
            last_cleanup = int(await self.db.get_metadata("last_cleanup", "0") or 0)
            interval = int(self.config.cleanup_interval_days) * 86400
            if now - last_cleanup > interval:
                removed = await cleanup_database(self.db)
                await self.db.set_metadata("last_cleanup", now)
                logger.info("AutoDJ-Cleanup abgeschlossen; entfernt: %s", removed)

        if _env_bool("LOCAL_AUTODJ_SCAN_ON_START", True):
            last_scan = int(await self.db.get_metadata("last_scan", "0") or 0)
            interval = int(self.config.scan_interval_days) * 86400
            if now - last_scan > interval:
                inserted, skipped = await scan_music_library(self.config, self.db)
                await self.db.set_metadata("last_scan", now)
                logger.info("AutoDJ-Scan abgeschlossen; neu: %s, übersprungen: %s", inserted, skipped)

        init_ui(self.bot, self.config, self.radio)
        init_player(
            self.bot,
            self.config,
            self.radio,
            update_now_playing,
            refresh_all_uis,
            cleanup_fn=force_new_embed,
        )

        if not self.radio.task or self.radio.task.done():
            self.radio.task = asyncio.create_task(radio_player(), name="local-autodj-player")

        try:
            genres = await self.radio.get_all_genres()
            self.bot.add_view(UnifiedStandbyView(self.radio))
            self.bot.add_view(FrequencyStationView(self.radio))
            self.bot.add_view(NowPlayingView(self.radio, genres=genres))
        except Exception as exc:
            logger.warning("AutoDJ Persistent Views konnten nicht registriert werden: %s", exc)

        if int(getattr(self.config, "radio_text_channel_id", 0) or 0) > 0:
            try:
                await force_new_embed()
            except Exception as exc:
                logger.warning("AutoDJ-UI konnte nicht initialisiert werden: %s", exc)

        self.background_tasks = [
            asyncio.create_task(self._embed_refresh_loop(), name="local-autodj-embed-refresh"),
            asyncio.create_task(self._progress_update_loop(), name="local-autodj-progress"),
        ]

        if _env_bool("LOCAL_AUTODJ_FILE_MONITOR", True):
            self.monitor = start_monitoring(self.config, self.db, asyncio.get_running_loop())

        self.initialized = True
        logger.info("Lokaler AutoDJ vollständig initialisiert.")

    async def _embed_refresh_loop(self) -> None:
        while not self.bot.is_closed():
            await asyncio.sleep(max(1, int(self.config.embed_refresh_minutes)) * 60)
            if int(getattr(self.config, "radio_text_channel_id", 0) or 0) <= 0:
                continue
            try:
                await force_new_embed()
            except Exception as exc:
                logger.warning("AutoDJ Embed-Refresh fehlgeschlagen: %s", exc)

    async def _progress_update_loop(self) -> None:
        while not self.bot.is_closed():
            await asyncio.sleep(max(5, int(self.config.progress_update_seconds)))
            if self.radio.status == RadioStatusEnum.PLAYING and self.radio.now_playing_message:
                try:
                    await update_now_playing(self.radio.current_song or {})
                except Exception:
                    pass

    async def activate(self, guild: discord.Guild, channel: discord.VoiceChannel) -> None:
        if not self.available:
            raise RuntimeError("Lokaler AutoDJ ist nicht vollständig konfiguriert.")
        if guild.id != int(self.config.guild_id):
            raise RuntimeError("Der lokale AutoDJ ist nur für die konfigurierte DISCORD_GUILD_ID verfügbar.")
        await self.initialize()
        self.radio.runtime_mode = "local_autodj"
        self.radio.voice_channel_id = channel.id
        self.radio.embed_manager.save_value("voice_channel_id", channel.id)
        self.radio.dispatch(RadioAction.JOIN, channel.id)

    async def deactivate(self, keep_voice: bool = True) -> None:
        if not self.available:
            return
        self.radio.runtime_mode = "inactive"
        self.radio.status = RadioStatusEnum.STOPPED
        self.radio.track_start_time = None
        self.radio.track_start_offset = 0.0
        voice = self.radio.voice
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()
        while not self.radio.action_queue.empty():
            try:
                self.radio.action_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        if not keep_voice and voice and voice.is_connected():
            await voice.disconnect(force=True)
            self.radio.voice = None
            self.radio.voice_channel_id = None

    async def skip(self) -> None:
        if not self.available:
            raise RuntimeError("Lokaler AutoDJ ist deaktiviert.")
        self.radio.dispatch(RadioAction.SKIP)

    async def pause(self) -> bool:
        if not self.available or self.radio.status != RadioStatusEnum.PLAYING:
            return False
        self.radio.dispatch(RadioAction.PAUSE)
        return True

    async def resume(self) -> bool:
        if not self.available or self.radio.status != RadioStatusEnum.PAUSED:
            return False
        self.radio.dispatch(RadioAction.REPLAY)
        return True

    async def set_volume(self, volume: float) -> None:
        if not self.available:
            return
        self.radio.dispatch(RadioAction.SET_VOLUME, max(0.0, min(volume, 2.0)))

    async def disconnect(self) -> None:
        if not self.available:
            return
        self.radio.dispatch(RadioAction.DISCONNECT)

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
        if not self.available or not self.bot.user:
            return

        if member.id == self.bot.user.id:
            if after.channel:
                self.radio.voice_channel_id = after.channel.id
                self.radio.voice = member.guild.voice_client
                self.radio.embed_manager.save_value("voice_channel_id", after.channel.id)
            elif before.channel:
                self.radio.voice_channel_id = None
                self.radio.voice = None
                self.radio.status = RadioStatusEnum.IDLE
                self.radio.current_song = None
                self.radio.embed_manager.save_value("voice_channel_id", None)
            return

        timeout = int(getattr(self.config, "afk_timeout_seconds", 0) or 0)
        if timeout <= 0:
            return
        voice_client = member.guild.voice_client
        if not voice_client or not voice_client.channel or self.radio.runtime_mode != "local_autodj":
            return
        humans = [m for m in voice_client.channel.members if not m.bot]
        if not humans and not self.radio.afk_task:
            async def afk_timer() -> None:
                try:
                    await asyncio.sleep(timeout)
                    current = member.guild.voice_client
                    if current and current.channel and not [m for m in current.channel.members if not m.bot]:
                        self.radio.dispatch(RadioAction.DISCONNECT, user=self.bot.user)
                except asyncio.CancelledError:
                    pass
                finally:
                    self.radio.afk_task = None
            self.radio.afk_task = asyncio.create_task(afk_timer(), name="local-autodj-afk")
        elif humans and self.radio.afk_task:
            self.radio.afk_task.cancel()
            self.radio.afk_task = None

    async def shutdown(self) -> None:
        """Beendet Monitor und Hintergrundtasks kontrolliert."""
        for task in self.background_tasks:
            task.cancel()
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        self.background_tasks = []
        if self.monitor:
            try:
                self.monitor.stop()
                self.monitor.join(timeout=5)
            except Exception as exc:
                logger.warning("AutoDJ-Dateimonitor konnte nicht sauber beendet werden: %s", exc)
            self.monitor = None

    def status(self) -> dict[str, Any]:
        if not self.available:
            return {
                "enabled": self.enabled,
                "available": False,
                "initialized": self.initialized,
                "reason": "DISCORD_GUILD_ID oder AutoDJ-Konfiguration fehlt",
            }
        return {
            "enabled": True,
            "available": True,
            "initialized": self.initialized,
            "guild_id": int(self.config.guild_id),
            "mode": self.radio.runtime_mode,
            "status": self.radio.status.name,
            "genre": self.radio.genre,
            "queue_length": len(self.radio.queue),
            "current_song": {
                "artist": (self.radio.current_song or {}).get("artist"),
                "title": (self.radio.current_song or {}).get("title"),
            } if self.radio.current_song else None,
        }
