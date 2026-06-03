import { ChannelType, PermissionFlagsBits } from 'discord.js';
import { handleAppManagerCommand } from './app-manager.js';

function userVoiceChannel(interaction) {
  const channel = interaction.member?.voice?.channel;
  if (!channel || channel.type !== ChannelType.GuildVoice) {
    throw new Error('Du musst in einem Voice Channel sein.');
  }
  return channel;
}

function hasRadioPermission(interaction) {
  return interaction.memberPermissions?.has(PermissionFlagsBits.ManageGuild)
    || interaction.memberPermissions?.has(PermissionFlagsBits.Connect);
}

export function createInteractionRouter({ radioCore, discordApi, logger }) {
  return async function routeInteraction(interaction) {
    if (!interaction.isChatInputCommand()) return;

    try {
      if (interaction.commandName === 'apps-list' || interaction.commandName === 'apps-remove') {
        await handleAppManagerCommand(interaction, { discordApi });
        return;
      }

      if (interaction.commandName !== 'radio') return;

      if (!interaction.inGuild()) {
        throw new Error('Radio Commands funktionieren nur auf einem Server.');
      }

      if (!hasRadioPermission(interaction)) {
        await interaction.reply({
          content: 'Du brauchst Connect oder Manage Server, um Radio Core zu steuern.',
          ephemeral: true
        });
        return;
      }

      const subcommand = interaction.options.getSubcommand();

      if (subcommand === 'play') {
        await interaction.deferReply();
        const voiceChannel = userVoiceChannel(interaction);
        const streamUrl = interaction.options.getString('stream_url')?.trim() || null;
        const stationName = interaction.options.getString('station_name')?.trim() || null;

        await radioCore.play({
          guild: interaction.guild,
          voiceChannel,
          streamUrl,
          stationName,
          requestedBy: interaction.user
        });

        await interaction.editReply({ embeds: [radioCore.statusEmbed()] });
        return;
      }

      if (subcommand === 'stop') {
        radioCore.stop({ reason: `requested-by-${interaction.user.id}` });
        await interaction.reply('Radio Core wurde gestoppt.');
        return;
      }

      if (subcommand === 'status') {
        await interaction.reply({ embeds: [radioCore.statusEmbed()] });
        return;
      }

      if (subcommand === 'reconnect') {
        await interaction.deferReply();
        await radioCore.reconnect(`requested-by-${interaction.user.id}`);
        await interaction.editReply({ embeds: [radioCore.statusEmbed()] });
        return;
      }

      if (subcommand === 'nowplaying') {
        const snapshot = radioCore.snapshot();
        const track = snapshot.current?.currentTrack || 'UNBEKANNT';
        await interaction.reply(`Now playing: **${track}**`);
      }
    } catch (error) {
      logger.error('Interaction handling failed.', error, {
        command: interaction.commandName
      });

      const message = `Fehler: ${error.message}`;
      if (interaction.deferred || interaction.replied) {
        await interaction.editReply(message).catch(() => {});
      } else {
        await interaction.reply({ content: message, ephemeral: true }).catch(() => {});
      }
    }
  };
}
