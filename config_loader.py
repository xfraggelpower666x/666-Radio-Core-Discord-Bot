from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "botconfig" / "autodj.json"
load_dotenv(BASE_DIR / ".env")


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_path(value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return str(path.resolve())


class Config:
    """Konfiguration der integrierten lokalen AutoDJ-Engine."""

    def __init__(self, data: dict[str, Any]):
        self.guild_id = _as_int(os.getenv("DISCORD_GUILD_ID") or data.get("guild_id"))
        self.voice_channel_id = _as_int(os.getenv("RADIO_VOICE_CHANNEL_ID", "").split(",")[0] or data.get("voice_channel_id"))
        self.auto_join_channel_id = _as_int(os.getenv("LOCAL_AUTODJ_VOICE_CHANNEL_ID") or data.get("auto_join_channel_id"))
        self.radio_text_channel_id = _as_int(os.getenv("RADIO_TEXT_CHANNEL_ID") or data.get("radio_text_channel_id"))
        self.feedback_channel_id = _as_int(data.get("feedback_channel_id"))
        self.afk_channel_id = _as_int(data.get("afk_channel_id"))
        self.default_genre = str(data.get("default_genre", "666SOUNDsDESIGn"))
        self.default_language = str(data.get("default_language", "de"))
        self.default_ui_mode = str(data.get("default_ui_mode", "full"))
        self.default_presence = str(data.get("default_presence", "666SOUNDsDESIGn AutoDJ bereit"))

        scanner = data.get("scanner", {})
        self.supported_extensions = set(scanner.get("supported_extensions", ["mp3", "flac", "wav", "ogg", "m4a", "aac"]))
        self.cover_filenames = scanner.get("cover_filenames", [
            "cover.jpg", "cover.png", "cover.jpeg", "folder.jpg", "folder.png", "front.jpg", "front.png"
        ])
        self.metadata_fields = scanner.get("metadata_fields", {
            "artist": ["artist", "ARTIST", "TPE1"],
            "title": ["title", "TITLE", "TIT2"],
            "album": ["album", "ALBUM", "TALB"],
            "date": ["date", "DATE", "year", "YEAR", "TDRC"],
            "label": ["organization", "ORGANIZATION", "TPUB"],
            "catnum": ["catalognumber", "CATALOGNUMBER", "TXXX:CATALOGNUMBER"],
            "mediatype": ["mediatype", "MEDIATYPE", "TMED"],
            "rating": ["rating", "RATING", "POPM"],
        })
        self.locales = scanner

        self.genres = {
            str(name): [_resolve_path(str(path)) for path in paths]
            for name, paths in data.get("genres", {}).items()
        }
        self.virtual_genres = data.get("virtual_genres", [])
        self.ffmpeg_path = str(os.getenv("FFMPEG_PATH") or data.get("ffmpeg_path", "ffmpeg"))
        self.admin_role_id = _as_int(os.getenv("DJ_ROLE_ID") or data.get("admin_role_id"))
        self.sysadmin_role_id = _as_int(data.get("sysadmin_role_id"))
        self.restricted_channels = {
            _as_int(k): _as_int(v) for k, v in data.get("restricted_channels", {}).items() if _as_int(k) and _as_int(v)
        }

        ui_settings = data.get("ui_settings", {})
        self.search_items_per_page = int(ui_settings.get("search_items_per_page", 5))
        self.history_items_per_page = int(ui_settings.get("history_items_per_page", 5))
        self.queue_items_per_page = int(ui_settings.get("queue_items_per_page", 5))
        self.playlist_items_per_page = int(ui_settings.get("playlist_items_per_page", 5))
        self.queue_refresh_limit = int(ui_settings.get("queue_refresh_limit", 11))
        self.player_upcoming_limit = int(ui_settings.get("player_upcoming_limit", 5))
        theme = ui_settings.get("theme", {})
        self.theme_primary = int(str(theme.get("primary", "0x9B30FF")), 16)
        self.theme_secondary = int(str(theme.get("secondary", "0x11131A")), 16)
        self.theme_success = int(str(theme.get("success", "0x00E5FF")), 16)
        self.theme_warning = int(str(theme.get("warning", "0xFEE75C")), 16)
        self.theme_danger = int(str(theme.get("danger", "0xFF2E88")), 16)
        self.theme_idle = int(str(theme.get("idle", "0xFF2E88")), 16)
        self.theme_paused = int(str(theme.get("paused", "0xFEE75C")), 16)
        self.theme_playing = int(str(theme.get("playing", "0x00E5FF")), 16)
        self.theme_background = int(str(theme.get("background", "0x11131A")), 16)
        self.theme_accent = int(str(theme.get("accent", "0x9B30FF")), 16)

        self.cleanup_interval_days = int(data.get("cleanup_interval_days", 14))
        self.scan_interval_days = int(data.get("scan_interval_days", 1))
        self.db_path = _resolve_path(str(data.get("db_path", "db/autodj.sqlite3")))

        timings = data.get("timings", {})
        self.embed_refresh_minutes = int(timings.get("embed_refresh_minutes", 58))
        self.progress_update_seconds = int(timings.get("progress_update_seconds", 15))
        self.history_save_seconds = int(timings.get("history_save_seconds", 2))
        self.play_count_threshold_percent = float(timings.get("play_count_threshold_percent", 0.1))
        self.error_retry_seconds = int(timings.get("error_retry_seconds", 5))
        self.afk_timeout_seconds = int(timings.get("afk_timeout_seconds", 0))

        defaults = data.get("defaults", {})
        self.default_volume = float(defaults.get("volume", 0.7))
        self.use_loudnorm = bool(defaults.get("use_loudnorm", False))
        self.autocomplete_limit = int(defaults.get("autocomplete_limit", 25))
        self.languages = data.get("languages", [
            {"code": "de", "label": "Deutsch", "emoji": "🇩🇪"},
            {"code": "en", "label": "English", "emoji": "🇬🇧"},
        ])
        self.token = os.getenv("DISCORD_TOKEN", "")

    def save_genres(self, new_genres: dict[str, list[str]]) -> None:
        self.genres = new_genres
        self._save_value("genres", new_genres)

    def save_config_value(self, key: str, value: Any) -> None:
        self._save_value(key, value)

    def _save_value(self, key: str, value: Any) -> None:
        data = _read_config()
        data[key] = value
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(CONFIG_PATH)

    def get_token(self) -> str:
        return self.token


def _read_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"AutoDJ-Konfiguration fehlt: {CONFIG_PATH}")
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config() -> Config:
    return Config(_read_config())
