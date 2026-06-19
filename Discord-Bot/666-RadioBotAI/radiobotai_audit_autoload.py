"""
666 RadioBotAI Audit Autoload
Phase 2C-15

This helper safely loads the Discord visual audit cog.
"""

from __future__ import annotations

import inspect


AUDIT_EXTENSION = "cogs.radiobotai_audit"


async def load_audit_cog(bot):
    """Load the audit cog once. Safe for discord.py / py-cord style bots."""
    try:
        extensions = getattr(bot, "extensions", {}) or {}
        if AUDIT_EXTENSION in extensions:
            return True, "already_loaded"

        result = bot.load_extension(AUDIT_EXTENSION)

        if inspect.isawaitable(result):
            await result

        return True, "loaded"

    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
