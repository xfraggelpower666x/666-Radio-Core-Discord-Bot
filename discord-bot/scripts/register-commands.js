/**
 * 666RadioCoreDJ | scripts/register-commands.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Registriert /radio Slash Commands im angegebenen Discord Server.
 */
const { REST, Routes } = require('discord.js');
const config = require('../src/config');
const { commands } = require('../src/discord/commands');

async function main() {
  if (!config.discord.token || !config.discord.clientId || !config.discord.guildId) {
    throw new Error('DISCORD_TOKEN, DISCORD_CLIENT_ID und DISCORD_GUILD_ID müssen in .env gesetzt sein.');
  }

  const rest = new REST({ version: '10' }).setToken(config.discord.token);
  await rest.put(
    Routes.applicationGuildCommands(config.discord.clientId, config.discord.guildId),
    { body: commands }
  );

  console.log('666RadioCoreDJ Slash Commands registriert.');
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
