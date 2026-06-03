import { PermissionFlagsBits, SlashCommandBuilder } from 'discord.js';

export function buildSlashCommands() {
  return [
    new SlashCommandBuilder()
      .setName('radio')
      .setDescription('Steuert den 666SOUNDsDESIGn Radio Core.')
      .addSubcommand(subcommand =>
        subcommand
          .setName('play')
          .setDescription('Startet Radio Playback im aktuellen Voice Channel.')
          .addStringOption(option =>
            option
              .setName('stream_url')
              .setDescription('Optionaler SHOUTcast/Icecast Stream URL.')
              .setRequired(false)
          )
          .addStringOption(option =>
            option
              .setName('station_name')
              .setDescription('Optionaler Sendername fuer Statusanzeigen.')
              .setRequired(false)
          )
      )
      .addSubcommand(subcommand =>
        subcommand
          .setName('stop')
          .setDescription('Stoppt Radio Playback und verlaesst den Voice Channel.')
      )
      .addSubcommand(subcommand =>
        subcommand
          .setName('status')
          .setDescription('Zeigt Broadcast-, Health- und Track-Status.')
      )
      .addSubcommand(subcommand =>
        subcommand
          .setName('reconnect')
          .setDescription('Erzwingt einen Reconnect zum Stream.')
      )
      .addSubcommand(subcommand =>
        subcommand
          .setName('nowplaying')
          .setDescription('Zeigt den aktuell erkannten ICY Track.')
      ),

    new SlashCommandBuilder()
      .setName('apps-list')
      .setDescription('Listet installierte Server-Integrationen/Apps auf.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild),

    new SlashCommandBuilder()
      .setName('apps-remove')
      .setDescription('Entfernt eine Server-Integration/App nach Bestaetigung.')
      .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
      .addStringOption(option =>
        option
          .setName('integration_id')
          .setDescription('ID der Integration aus /apps-list.')
          .setRequired(true)
      )
      .addBooleanOption(option =>
        option
          .setName('confirm')
          .setDescription('Muss true sein, sonst wird nichts geloescht.')
          .setRequired(true)
      )
  ].map(command => command.toJSON());
}
