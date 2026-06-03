import 'dotenv/config';
import { REST, Routes } from 'discord.js';
import { loadEnv } from './config/env.js';
import { buildSlashCommands } from './commands/definitions.js';

const config = loadEnv();
const commands = buildSlashCommands();
const rest = new REST({ version: '10' }).setToken(config.discordToken);

try {
  if (config.guildId) {
    await rest.put(
      Routes.applicationGuildCommands(config.clientId, config.guildId),
      { body: commands }
    );
    console.log(`Slash Commands for guild ${config.guildId} registered.`);
  } else {
    await rest.put(
      Routes.applicationCommands(config.clientId),
      { body: commands }
    );
    console.log('Global slash commands registered. Discord propagation can take time.');
  }
} catch (error) {
  console.error('Command deployment failed:', error);
  process.exit(1);
}
