"""Compatibility shim for the Vocard `voicelink` runtime.

The 666 RadioBotAI add-on modules (`radiobotai_permissions`,
`radiobotai_runtime_status`) are designed to run inside a Vocard fork that
ships an in-tree `voicelink` package. That package is NOT published on PyPI and
is NOT part of this repository payload, so a bare `from voicelink import ...`
fails with ModuleNotFoundError whenever the add-on is imported, linted, or
unit-tested outside the full Vocard host (e.g. CI, the Lite deploy).

This shim re-exports the real `voicelink.Config` / `voicelink.MongoDBHandler`
when the host runtime is present, and otherwise falls back to env-driven
defaults that expose the same attributes the add-on code reads. This keeps the
add-on import-safe everywhere while remaining a no-op when Vocard IS installed.
"""

from __future__ import annotations

import os

try:
    from voicelink import Config as Config  # type: ignore
    from voicelink import MongoDBHandler as MongoDBHandler  # type: ignore
    VOICELINK_AVAILABLE = True
except ModuleNotFoundError:
    VOICELINK_AVAILABLE = False

    def _parse_ids(raw: str) -> list[int]:
        ids: list[int] = []
        for part in raw.replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ids.append(int(part))
            except ValueError:
                continue
        return ids

    class Config:  # type: ignore[no-redef]
        """Minimal env-backed stand-in for `voicelink.Config`."""

        version = os.getenv("RADIOBOTAI_VERSION", "0.0.0-standalone")

        def __init__(self) -> None:
            admin_role = os.getenv("RADIO_ADMIN_ROLE_ID", "0")
            self.radio = {
                "bot_name": os.getenv("RADIO_BOT_NAME", "666 RadioBotAI"),
                "stream_url": os.getenv("RADIO_STREAM_URL", ""),
                "allowed_role_ids": _parse_ids(os.getenv("RADIO_ALLOWED_ROLE_IDS", "")),
                "radio_admin_role_id": int(admin_role) if admin_role.isdigit() else 0,
            }
            self.bot_access_user = _parse_ids(os.getenv("RADIO_BOT_ACCESS_USERS", ""))

    class MongoDBHandler:  # type: ignore[no-redef]
        """No-op stand-in; returns empty settings without a Vocard/Mongo host."""

        @staticmethod
        def get_cached_settings(guild_id: int) -> dict:
            return {}


__all__ = ["Config", "MongoDBHandler", "VOICELINK_AVAILABLE"]
