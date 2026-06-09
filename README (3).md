# ============================================================
# 666 RadioBotAI / Vocard Sovereign Dashboard
# Beispiel ohne echte Secrets
# ============================================================

PUBLIC_PROJECT_NAME="666SOUNDsDESIGn WebRadio"
PUBLIC_BOT_NAME="666 RadioBotAI"
PUBLIC_VERSION="v1.1.0"
PUBLIC_WEBRADIO_BASE_URL="https://webradio.666soundsdesign-broadcaster.com"
PUBLIC_MAIN_STREAM_URL="https://webradio.666soundsdesign-broadcaster.com/stream"
PUBLIC_FALLBACK_STREAM_URL="https://webradio.666soundsdesign-broadcaster.com/fallback-stream"
PUBLIC_NOWPLAYING_URL="https://webradio.666soundsdesign-broadcaster.com/api/nowplaying"
PUBLIC_HEALTH_URL="https://webradio.666soundsdesign-broadcaster.com/health"
PUBLIC_TUNEIN_URL="https://tunein.com/radio/s357001"

# Discord Bot Runtime - nicht in GitHub mit echten Werten committen
DISCORD_TOKEN="replace_with_discord_bot_token"
DISCORD_CLIENT_ID="replace_with_discord_client_id"
DISCORD_GUILD_ID="replace_with_discord_guild_id"

# Dashboard/Admin - echte Werte als Cloudflare Secrets oder Host ENV setzen
DISCORD_ADMIN_TOKEN="replace_with_admin_token"
DISCORD_GATE_CODE="replace_with_gate_code"
ADMIN_AUTH_VERIFY_URL="https://666-system-auth.666soundsdesign-broadcaster.com/verify"

# Optional: vorhandene WebRadio Discord-Shooter-Endpunkte als Bridge nutzen
DISCORD_SHOOTER_STATUS_URL="https://webradio.666soundsdesign-broadcaster.com/api/discord/status"
DISCORD_SHOOTER_MANUAL_URL="https://webradio.666soundsdesign-broadcaster.com/api/discord/manual"
DISCORD_SHOOTER_MESSAGE_URL="https://webradio.666soundsdesign-broadcaster.com/api/discord/message"
DISCORD_SHOOTER_NOWPLAYING_URL="https://webradio.666soundsdesign-broadcaster.com/api/discord/nowplaying"

# Volume Standard
BOT_VOLUME_DEFAULT=100
BOT_VOLUME_MIN=0
BOT_VOLUME_SAFE_MAX=150
BOT_VOLUME_MAX=200
