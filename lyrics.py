"""MIT License

Copyright (c) 2023 - present Vocard Development

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os

from pathlib import Path
from dotenv import load_dotenv
from typing import (
    Dict,
    List,
    Any,
    Union,
    Optional
)

from .enums import SearchType

load_dotenv()

class Config:
    _instance: Optional['Config'] = None
    WORKING_DIR: Path = Path(__file__).resolve().parent.parent
    LAST_SESSION_FILE_DIR: str = WORKING_DIR / "last-session.json"

    def __new__(cls, settings: Dict[str, Any] = None) -> 'Config':
        """
        Singleton pattern to ensure only one instance of Config exists.
        If settings are provided, creates a new instance that replaces the old one.
        
        Args:
            settings (Dict[str, Any], optional): A dictionary containing configuration settings. Defaults to None.
                                               If provided, creates a new instance that replaces the old one.
        """
        if settings is not None:
            instance = super(Config, cls).__new__(cls)
            instance.__init__(settings)
            cls._instance = instance
            return instance
            
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            
        return cls._instance

    def __init__(self, settings: Dict[str, Any] = None) -> None:
        """
        Initialize configuration settings. 
        
        Args:
            settings (Dict[str, Any], optional): A dictionary containing configuration settings.
                                               If None, uses empty dict with default values.
        """
        if hasattr(self, 'initialized'):
            return
            
        settings = settings or {}

        def _env(*names: str, default=None):
            for name in names:
                value = os.getenv(name)
                if value not in (None, ""):
                    return value
            return default

        def _int(value, default: int = 0) -> int:
            try:
                if value in (None, ""):
                    return default
                return int(value)
            except (TypeError, ValueError):
                return default

        def _bool(value, default: bool = False) -> bool:
            if value in (None, ""):
                return default
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("1", "true", "yes", "y", "on")

        def _int_list(value) -> List[int]:
            if not value:
                return []
            if isinstance(value, list):
                return [_int(v) for v in value if _int(v)]
            return [_int(v.strip()) for v in str(value).split(",") if _int(v.strip())]
        
        self.token: str = settings.get("token") or _env("DISCORD_TOKEN", "TOKEN", default="")
        self.client_id: int = _int(settings.get("client_id") or _env("DISCORD_CLIENT_ID", "CLIENT_ID"), 0)
        self.genius_token: str = settings.get("genius_token") or _env("GENIUS_TOKEN", default="")
        self.mongodb_url: str = _env("MONGODB_URL") or settings.get("mongodb_url") or "mongodb://mongo:27017"
        self.mongodb_name: str = _env("MONGODB_NAME") or settings.get("mongodb_name") or "radio_bot_ai"
        
        self.invite_link: str = settings.get("invite_link") or "https://discord.com/oauth2/authorize"
        self.nodes: Dict[str, Dict[str, Union[str, int, bool]]] = settings.get("nodes", {})
        if _env("LAVALINK_HOST") or _env("LAVALINK_PORT") or _env("LAVALINK_PASSWORD"):
            self.nodes = {
                "DEFAULT": {
                    **self.nodes.get("DEFAULT", {}),
                    "host": _env("LAVALINK_HOST", default=self.nodes.get("DEFAULT", {}).get("host", "lavalink")),
                    "port": _int(_env("LAVALINK_PORT", default=self.nodes.get("DEFAULT", {}).get("port", 2333)), 2333),
                    "password": _env("LAVALINK_PASSWORD", default=self.nodes.get("DEFAULT", {}).get("password", "youshallnotpass")),
                    "secure": _bool(_env("LAVALINK_SECURE", default=self.nodes.get("DEFAULT", {}).get("secure", False))),
                    "identifier": self.nodes.get("DEFAULT", {}).get("identifier", "DEFAULT"),
                }
            }
        self.max_queue: int = settings.get("default_max_queue", 1000)
        self.search_platform: SearchType = SearchType.from_platform(settings.get("default_search_platform", "youtube")) or SearchType.YOUTUBE
        self.bot_prefix: str = settings.get("prefix", "")
        self.activity: List[Dict[str, str]] = settings.get("activity", [{"listen": "/help"}])
        self.logging: Dict[Union[str, Dict[str, Union[str, bool]]]] = settings.get("logging", {})
        self.embed_color: str = int(settings.get("embed_color", "0xb3b3b3"), 16)
        self.bot_access_user: List[int] = settings.get("bot_access_user", [])
        self.sources_settings: Dict[Dict[str, str]] = settings.get("sources_settings", {})
        self.cooldowns_settings: Dict[str, List[int]] = settings.get("cooldowns", {})
        self.aliases_settings: Dict[str, List[str]] = settings.get("aliases", {})
        self.controller: Dict[str, Dict[str, Any]] = settings.get("default_controller", {})
        self.voice_status_template: str = settings.get("default_voice_status_template", "")
        self.lyrics_platform: str = settings.get("lyrics_platform", "A_ZLyrics").lower()
        self.ipc_client: Dict[str, Union[str, bool, int]] = settings.get("ipc_client", {})
        self.playlist_settings: Dict[str, Union[str, int]] = settings.get("playlist_settings", {})
        self.timer_settings: Dict[str, int] = settings.get("timer_settings", {})
        self.version: str = settings.get("version", "")
        self.disable_update_check: bool = _bool(settings.get("disable_update_check", _env("RADIO_DISABLE_UPDATE_CHECK")), True)
        self.sync_commands_on_start: bool = _bool(settings.get("sync_commands_on_start", _env("RADIO_SYNC_COMMANDS_ON_START")), True)

        radio_settings: Dict[str, Any] = settings.get("radio", {}) or {}
        self.radio: Dict[str, Any] = {
            "bot_name": _env("RADIO_BOT_NAME") or radio_settings.get("bot_name") or "666 RadioBotAI",
            "project_name": _env("RADIO_PROJECT_NAME") or radio_settings.get("project_name") or "666SOUNDsDESIGn WebRadio",
            "stream_url": _env("RADIO_STREAM_URL") or radio_settings.get("stream_url") or "",
            "stream_title": _env("RADIO_STREAM_TITLE") or radio_settings.get("stream_title") or "666SOUNDsDESIGn WebRadio Stream",
            "default_voice_channel_id": _int(_env("RADIO_VOICE_CHANNEL_ID") or radio_settings.get("default_voice_channel_id"), 0),
            "log_text_channel_id": _int(_env("RADIO_LOG_TEXT_CHANNEL_ID") or radio_settings.get("log_text_channel_id"), 0),
            "admin_role_id": _int(_env("RADIO_ADMIN_ROLE_ID") or radio_settings.get("admin_role_id"), 0),
            "admin_role_name": _env("RADIO_ADMIN_ROLE_NAME") or radio_settings.get("admin_role_name") or "666 RadioBotAI Admin",
            "allowed_role_ids": _int_list(_env("RADIO_ALLOWED_ROLE_IDS") or radio_settings.get("allowed_role_ids")),
            "default_volume": _int(_env("RADIO_DEFAULT_VOLUME") or radio_settings.get("default_volume"), 80),
            "auto_reconnect": _bool(_env("RADIO_AUTO_RECONNECT") or radio_settings.get("auto_reconnect"), True),
            "controller_info_button": _bool(_env("RADIO_CONTROLLER_INFO_BUTTON") or radio_settings.get("controller_info_button"), True),
        }
        
        self.initialized = True
    
    @classmethod
    def get_source_config(cls, source: str, type: str) -> Union[str, None]:
        """
        Get source configuration for a specific source and type.
        
        Args:
            source (str): The source identifier (e.g., 'youtube', 'spotify').
                            Case-insensitive and spaces are removed.
            type (str): The type of configuration to retrieve (e.g., 'emoji', 'color').
        
        Returns:
            Union[str, None]: The configuration value for the specified source and type.
                            Returns None if either the source or type doesn't exist.
        
        Example:
            >>> Config().get_source("youtube", "emoji")
            "🎵"
        """
        if not isinstance(source, str) or not isinstance(type, str):
            return None
            
        normalized_source: str = source.lower().strip().replace(" ", "")
        source_settings: dict[str, str] = cls._instance.sources_settings.get(
            normalized_source,
            cls._instance.sources_settings.get("others", {})
        )
        
        return source_settings.get(type)
    
    @classmethod
    def get_playlist_config(cls) -> tuple[int, int, str]:
        config = cls._instance.playlist_settings
        return config.get("max_playlists", 5), config.get("max_tracks_per_playlist", 500), config.get("default_playlist_name", "Favourite")