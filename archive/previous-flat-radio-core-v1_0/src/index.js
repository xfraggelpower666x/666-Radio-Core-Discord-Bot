import 'dotenv/config';
import { ActivityType, Client, GatewayIntentBits } from 'discord.js';
import { loadEnv, redactedConfig } from './config/env.js';
import { createInteractionRouter } from './commands/router.js';
import { DiscordApi } from './services/discord-api.js';
import { BotLogger } from './services/logger.js';
import { RadioCore } from './services/radio-core.js';

let config;
try {
  config = loadEnv();
} catch (error) {
  console.error(error.message);
  process.exit(1);
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildVoiceStates
  ]
});

const logger = new BotLogger({ client, logChannelId: config.logChannelId });
const discordApi = new DiscordApi({ token: config.discordToken });
const radioCore = new RadioCore({ client, config, logger });

client.once('ready', async () => {
  console.log(`Online as ${client.user.tag}`);
  console.log('Loaded config:', redactedConfig(config));

  client.user.setPresence({
    activities: [
      {
        name: '666SOUNDsDESIGn Radio Core',
        type: ActivityType.Listening
      }
    ],
    status: 'online'
  });

  await logger.info('Bot is online.', {
    user: client.user.tag,
    guilds: client.guilds.cache.size
  });
});

client.on('interactionCreate', createInteractionRouter({
  radioCore,
  discordApi,
  logger
}));

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

async function shutdown(signal) {
  logger.warn('Shutdown requested.', { signal });
  radioCore.stop({ reason: signal });
  client.destroy();
  process.exit(0);
}

client.login(config.discordToken);
