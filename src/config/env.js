const DEFAULT_HEALTH_INTERVAL_MS = 30_000;
const DEFAULT_HEALTH_TIMEOUT_MS = 10_000;

function readBoolean(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return ['1', 'true', 'yes', 'on'].includes(String(value).toLowerCase());
}

function readPositiveInteger(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function readNonNegativeInteger(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
}

export function loadEnv(env = process.env) {
  const missing = [];
  if (!env.DISCORD_TOKEN) missing.push('DISCORD_TOKEN');
  if (!env.CLIENT_ID) missing.push('CLIENT_ID');

  if (missing.length > 0) {
    throw new Error(`Missing required environment variable(s): ${missing.join(', ')}`);
  }

  return {
    discordToken: env.DISCORD_TOKEN,
    clientId: env.CLIENT_ID,
    guildId: env.GUILD_ID || null,
    logChannelId: env.LOG_CHANNEL_ID || null,
    defaultStreamUrl: env.RADIO_STREAM_URL || null,
    defaultStationName: env.RADIO_STATION_NAME || '666SOUNDsDESIGn Radio Core',
    streamHealthIntervalMs: readPositiveInteger(
      env.STREAM_HEALTH_INTERVAL_MS,
      DEFAULT_HEALTH_INTERVAL_MS
    ),
    streamHealthTimeoutMs: readPositiveInteger(
      env.STREAM_HEALTH_TIMEOUT_MS,
      DEFAULT_HEALTH_TIMEOUT_MS
    ),
    autoReconnect: readBoolean(env.AUTO_RECONNECT, true),
    maxReconnectAttempts: readNonNegativeInteger(env.MAX_RECONNECT_ATTEMPTS, 0)
  };
}

export function redactedConfig(config) {
  return {
    ...config,
    discordToken: config.discordToken ? '[redacted]' : null
  };
}
