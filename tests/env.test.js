import test from 'node:test';
import assert from 'node:assert/strict';
import { loadEnv, redactedConfig } from '../src/config/env.js';

test('loadEnv requires Discord token and client id', () => {
  assert.throws(() => loadEnv({}), /DISCORD_TOKEN, CLIENT_ID/);
});

test('loadEnv parses optional runtime settings', () => {
  const config = loadEnv({
    DISCORD_TOKEN: 'secret',
    CLIENT_ID: 'client',
    AUTO_RECONNECT: 'false',
    MAX_RECONNECT_ATTEMPTS: '3',
    STREAM_HEALTH_INTERVAL_MS: '15000'
  });

  assert.equal(config.autoReconnect, false);
  assert.equal(config.maxReconnectAttempts, 3);
  assert.equal(config.streamHealthIntervalMs, 15000);
  assert.equal(redactedConfig(config).discordToken, '[redacted]');
});
