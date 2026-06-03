/**
 * 666RadioCoreDJ | src/discord/permissions.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Rollen-/Channel-Gate für Radio-Control-Aktionen.
 */
const { PermissionFlagsBits } = require('discord.js');

function isAllowed(interaction, config) {
  if (!interaction || !interaction.member) return false;

  if (config.discord.textChannelId && interaction.channelId !== config.discord.textChannelId) {
    return false;
  }

  const roleIds = config.discord.allowedRoleIds || [];
  if (roleIds.length > 0) {
    return interaction.member.roles.cache.some((role) => roleIds.includes(role.id));
  }

  // Sicherheitsfallback: Wenn keine Rollen konfiguriert sind, dürfen nur Server-Manager steuern.
  return interaction.member.permissions.has(PermissionFlagsBits.ManageGuild);
}

function deniedMessage(config) {
  if (config.discord.textChannelId) {
    return 'Zugriff verweigert. Dieser Radio-Control-Befehl ist nur im freigegebenen Radio-Channel und mit erlaubter Rolle nutzbar.';
  }
  return 'Zugriff verweigert. Erlaubte Rolle fehlt oder der Server-Manager-Fallback greift nicht.';
}

module.exports = { isAllowed, deniedMessage };
