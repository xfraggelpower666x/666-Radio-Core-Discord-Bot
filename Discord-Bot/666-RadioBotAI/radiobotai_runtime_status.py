"""Runtime status helper for 666 RadioBotAI add-on cogs."""

from __future__ import annotations

import os
import time

from radiobotai_voicelink_compat import Config


STARTED_AT = time.time()


def runtime_status() -> dict:
    now = time.time()
    return {
        "ok": True,
        "uptime_seconds": int(now - STARTED_AT),
        "worker_url": os.getenv("RADIOBOTAI_WORKER_URL", "https://666radiobotai.666soundsdesign-broadcaster.com"),
        "admin_token_configured": bool(os.getenv("RADIOBOTAI_ADMIN_TOKEN")),
        "bot_name": Config().radio.get("bot_name", "666 RadioBotAI"),
        "stream_url_configured": bool(Config().radio.get("stream_url")),
        "version": Config().version,
    }
