import { EmbedBuilder, PermissionFlagsBits } from 'discord.js';

function assertGuildInteraction(interaction) {
  if (!interaction.guildId) {
    throw new Error('Dieser Command funktioniert nur auf einem Server.');
  }
}

function hasManageGuild(interaction) {
  return interaction.memberPermissions?.has(PermissionFlagsBits.ManageGuild);
}

function formatIntegration(integration) {
  const appName = integration.application?.name || 'Keine Application-Daten';
  const accountName = integration.account?.name || 'Kein Account';
  return [
    `**Name:** ${integration.name || appName}`,
    `**ID:** \`${integration.id}\``,
    `**Typ:** ${integration.type || 'unbekannt'}`,
    `**App:** ${appName}`,
    `**Account:** ${accountName}`,
    `**Aktiv:** ${integration.enabled ? 'ja' : 'nein'}`
  ].join('\n');
}

export async function handleAppManagerCommand(interaction, { discordApi }) {
  assertGuildInteraction(interaction);

  if (!hasManageGuild(interaction)) {
    await interaction.reply({
      content: 'Du brauchst Manage Server / MANAGE_GUILD, um diesen Command zu nutzen.',
      ephemeral: true
    });
    return;
  }

  if (interaction.commandName === 'apps-list') {
    await interaction.deferReply({ ephemeral: true });

    const integrations = await discordApi.request(`/guilds/${interaction.guildId}/integrations`, {
      method: 'GET'
    });

    if (!Array.isArray(integrations) || integrations.length === 0) {
      await interaction.editReply('Keine Guild-Integrationen gefunden.');
      return;
    }

    const chunks = integrations.slice(0, 10).map(formatIntegration);
    const embed = new EmbedBuilder()
      .setTitle('Installierte Server-Integrationen / Apps')
      .setDescription(chunks.join('\n\n---\n\n'))
      .setFooter({
        text: integrations.length > 10
          ? `Zeige 10 von ${integrations.length}.`
          : `${integrations.length} Eintraege gefunden.`
      });

    await interaction.editReply({ embeds: [embed] });
    return;
  }

  if (interaction.commandName === 'apps-remove') {
    await interaction.deferReply({ ephemeral: true });

    const integrationId = interaction.options.getString('integration_id', true).trim();
    const confirm = interaction.options.getBoolean('confirm', true);

    if (!confirm) {
      await interaction.editReply('Abgebrochen. Zum Loeschen muss confirm:true gesetzt werden.');
      return;
    }

    await discordApi.request(`/guilds/${interaction.guildId}/integrations/${integrationId}`, {
      method: 'DELETE',
      headers: {
        'X-Audit-Log-Reason': encodeURIComponent(
          `Removed by ${interaction.user.tag} using 666 Radio Core App Manager module`
        )
      }
    });

    await interaction.editReply(`Integration \`${integrationId}\` wurde entfernt.`);
  }
}
