"""666 RadioBotAI permission helpers for AI/Add-on cogs."""

from __future__ import annotations

from typing import Any

from radiobotai_voicelink_compat import Config, MongoDBHandler


def _member_from_ctx(ctx: Any):
    return getattr(ctx, "author", None) or getattr(ctx, "user", None)


def _guild_from_ctx(ctx: Any):
    return getattr(ctx, "guild", None)


def _role_ids(member: Any) -> set[int]:
    return {int(role.id) for role in getattr(member, "roles", []) if getattr(role, "id", None)}


def _configured_role_ids(settings: dict | None = None) -> set[int]:
    settings = settings or {}
    role_ids = {int(x) for x in Config().radio.get("allowed_role_ids", []) if x}
    for key in ("radio_admin_role_id", "admin_role_id", "dj"):
        value = settings.get(key) or Config().radio.get(key)
        try:
            if value:
                role_ids.add(int(value))
        except (TypeError, ValueError):
            continue
    return role_ids


def _has_manage_permission(member: Any) -> bool:
    perms = getattr(member, "guild_permissions", None)
    return bool(
        getattr(perms, "administrator", False)
        or getattr(perms, "manage_guild", False)
    )


def is_dj_member(member: Any, settings: dict | None = None) -> bool:
    if not member:
        return False

    try:
        if int(member.id) in Config().bot_access_user:
            return True
    except (TypeError, ValueError):
        pass

    if _has_manage_permission(member):
        return True

    configured = _configured_role_ids(settings)
    return bool(configured and (_role_ids(member) & configured))


def permission_status(ctx: Any) -> dict:
    member = _member_from_ctx(ctx)
    guild = _guild_from_ctx(ctx)
    settings = {}
    if guild:
        try:
            settings = MongoDBHandler.get_cached_settings(int(guild.id))
        except Exception:
            settings = {}

    return {
        "guild_id": getattr(guild, "id", None),
        "user_id": getattr(member, "id", None),
        "current_user_admin": _has_manage_permission(member),
        "current_user_dj": is_dj_member(member, settings),
        "configured_role_ids": sorted(_configured_role_ids(settings)),
    }


async def require_dj(ctx: Any) -> bool:
    status = permission_status(ctx)
    if status["current_user_dj"]:
        return True

    message = "Keine RadioBotAI-DJ/Adminberechtigung fuer diese Aktion."
    reply = getattr(ctx, "reply", None)
    if callable(reply):
        try:
            await reply(message, ephemeral=True)
        except TypeError:
            await reply(message)
        return False

    response = getattr(ctx, "response", None)
    if response and hasattr(response, "send_message"):
        await response.send_message(message, ephemeral=True)
    return False
