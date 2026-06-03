/**
 * 666RadioCoreDJ | src/config.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Zentrale Konfiguration aus .env laden, ohne Secrets zu loggen.
 * Änderung v1.3.0: Stream-Presets, Default-Preset, Voice-Volume und Volume-Grenzen ergänzt.
 */
const dotenv = require('dotenv');
dotenv.config();

function list(value) {
  return String(value || '')
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function bool(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return ['1', 'true', 'yes', 'ja', 'on'].includes(String(value).toLowerCase());
}

function int(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clampInt(value, fallback, min, max) {
  const parsed = int(value, fallback);
  return Math.max(min, Math.min(max, parsed));
}

function buildStreamPresets() {
  const presets = [];

  for (let index = 1; index <= 5; index += 1) {
    const id = String(index);
    const name = process.env[`STREAM_PRESET_${index}_NAME`] || `Stream ${index}`;
    const url = process.env[`STREAM_PRESET_${index}_URL`] || '';
    const volumePercent = clampInt(process.env[`STREAM_PRESET_${index}_VOLUME_PERCENT`], 0, 0, 200);

    presets.push({
      id,
      name,
      url,
      volumePercent: volumePercent > 0 ? volumePercent : null
    });
  }

  return presets;
}

const defaultVolumePercent = clampInt(process.env.VOICE_DEFAULT_VOLUME_PERCENT, 80, 0, 200);
const maxVolumePercent = clampInt(process.env.VOICE_MAX_VOLUME_PERCENT, 200, 1, 200);

const config = {
  app: {
    name: '666RadioCoreDJ',
    version: '1.3.0',
    activity: process.env.BOT_ACTIVITY || '666RadioCoreDJ',
    prefix: process.env.BOT_PREFIX || '!radio',
    controlPanelTitle: process.env.CONTROL_PANEL_TITLE || '666RadioCoreDJ Control',
    logLevel: process.env.LOG_LEVEL || 'info'
  },
  discord: {
    token: process.env.DISCORD_TOKEN || '',
    clientId: process.env.DISCORD_CLIENT_ID || '',
    guildId: process.env.DISCORD_GUILD_ID || '',
    textChannelId: process.env.RADIO_TEXT_CHANNEL_ID || '',
    allowedRoleIds: list(process.env.ALLOWED_ROLE_IDS)
  },
  cooldowns: {
    skipSeconds: int(process.env.SKIP_COOLDOWN_SECONDS, 60),
    jingleSeconds: int(process.env.JINGLE_COOLDOWN_SECONDS, 20)
  },
  sonicPanel: {
    panelUrl: process.env.SONICPANEL_PANEL_URL || '',
    djUser: process.env.SONICPANEL_DJ_USER || '',
    djPass: process.env.SONICPANEL_DJ_PASS || '',
    skipUrl: process.env.SONICPANEL_SKIP_URL || '',
    skipMethod: process.env.SONICPANEL_SKIP_METHOD || 'POST',
    skipAuth: process.env.SONICPANEL_SKIP_AUTH || 'none',
    skipBearerToken: process.env.SONICPANEL_SKIP_BEARER_TOKEN || '',
    jingleUrlTemplate: process.env.SONICPANEL_JINGLE_URL_TEMPLATE || '',
    jingleMethod: process.env.SONICPANEL_JINGLE_METHOD || 'POST',
    jingleAuth: process.env.SONICPANEL_JINGLE_AUTH || 'none',
    jingleBearerToken: process.env.SONICPANEL_JINGLE_BEARER_TOKEN || ''
  },
  radioControl: {
    primary: process.env.RADIO_SKIP_PRIMARY || 'direct_sonicpanel',
    fallback: process.env.RADIO_SKIP_FALLBACK || 'disabled'
  },
  shoutcast: {
    adminCgiUrl: process.env.SHOUTCAST_ADMIN_CGI_URL || '',
    sid: process.env.SHOUTCAST_SID || '1',
    adminUser: process.env.SHOUTCAST_ADMIN_USER || 'admin',
    adminPass: process.env.SHOUTCAST_ADMIN_PASS || '',
    passQueryEnabled: bool(process.env.SHOUTCAST_PASS_QUERY_ENABLED, false)
  },
  voiceRelay: {
    enabled: bool(process.env.VOICE_RELAY_ENABLED, false),
    channelId: process.env.VOICE_CHANNEL_ID || '',
    streamUrl: process.env.RADIO_STREAM_URL || '',
    defaultPreset: process.env.VOICE_DEFAULT_PRESET || '1',
    presets: buildStreamPresets(),
    bitrate: int(process.env.RADIO_STREAM_BITRATE, 128000),
    reconnectSeconds: int(process.env.VOICE_RECONNECT_SECONDS, 10),
    defaultVolumePercent,
    maxVolumePercent
  }
};

module.exports = config;
