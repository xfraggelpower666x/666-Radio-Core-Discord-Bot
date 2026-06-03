/**
 * 666RadioCoreDJ | src/index.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Discord-Bot-Hauptlogik für SonicPanel/MyIDJ AutoDJ-Skip, Jingle/ID und Voice-Stream-Steuerung.
 * Änderung v1.3.0: /pause, /resume, /volume, 5 Stream-Preset-Buttons und Preset-Auswahl über /play ergänzt.
 */
const {
  Client,
  GatewayIntentBits,
  Events
} = require('discord.js');
const config = require('./config');
const logger = require('./utils/logger');
const { RadioController } = require('./radio/radioController');
const { buildControlPanel } = require('./discord/panel');
const { isAllowed, deniedMessage } = require('./discord/permissions');
const { resultEmbed, statusEmbed } = require('./discord/replies');
const { VoiceRelayManager } = require('./voice/voiceRelay');

if (!config.discord.token) {
  logger.error('DISCORD_TOKEN fehlt. Bitte .env aus .env.example erstellen.');
  process.exit(1);
}

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildVoiceStates]
});

const radioController = new RadioController(config);
const voiceRelay = new VoiceRelayManager(config);

client.once(Events.ClientReady, async (readyClient) => {
  logger.info(`Connected as ${readyClient.user.tag}`);
  readyClient.user.setActivity(config.app.activity);

  try {
    await voiceRelay.startAutoRelay(readyClient);
  } catch (error) {
    logger.error(`Voice auto-relay failed: ${error.message}`);
  }
});

async function guardInteraction(interaction) {
  if (!isAllowed(interaction, config)) {
    await interaction.reply({ content: deniedMessage(config), ephemeral: true });
    return false;
  }
  return true;
}

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (!interaction.isChatInputCommand() && !interaction.isButton()) return;

    if (interaction.isChatInputCommand() && interaction.commandName === 'play') {
      if (!(await guardInteraction(interaction))) return;
      await interaction.deferReply({ ephemeral: true });
      const preset = interaction.options.getString('preset', false);
      const result = await voiceRelay.playFromInteraction(interaction, preset);
      await interaction.editReply(resultEmbed('Voice Stream /play', result));
      return;
    }

    if (interaction.isChatInputCommand() && interaction.commandName === 'pause') {
      if (!(await guardInteraction(interaction))) return;
      await interaction.deferReply({ ephemeral: true });
      const result = await voiceRelay.pauseFromInteraction(interaction);
      await interaction.editReply(resultEmbed('Voice Stream /pause', result));
      return;
    }

    if (interaction.isChatInputCommand() && interaction.commandName === 'resume') {
      if (!(await guardInteraction(interaction))) return;
      await interaction.deferReply({ ephemeral: true });
      const result = await voiceRelay.resumeFromInteraction(interaction);
      await interaction.editReply(resultEmbed('Voice Stream /resume', result));
      return;
    }

    if (interaction.isChatInputCommand() && interaction.commandName === 'stop') {
      if (!(await guardInteraction(interaction))) return;
      await interaction.deferReply({ ephemeral: true });
      const result = await voiceRelay.stopFromInteraction(interaction);
      await interaction.editReply(resultEmbed('Voice Stream /stop', result));
      return;
    }

    if (interaction.isChatInputCommand() && interaction.commandName === 'volume') {
      if (!(await guardInteraction(interaction))) return;
      await interaction.deferReply({ ephemeral: true });
      const result = await voiceRelay.setVolumeFromInteraction(interaction);
      await interaction.editReply(resultEmbed('Voice Stream /volume', result));
      return;
    }

    if (interaction.isChatInputCommand() && interaction.commandName === 'radio') {
      if (!(await guardInteraction(interaction))) return;

      const subcommand = interaction.options.getSubcommand();
      const context = {
        userId: interaction.user.id,
        userTag: interaction.user.tag
      };

      if (subcommand === 'panel') {
        await interaction.reply({ content: '666RadioCoreDJ Panel wird erstellt.', ephemeral: true });
        await interaction.channel.send(buildControlPanel(config));
        return;
      }

      if (subcommand === 'status') {
        await interaction.reply(statusEmbed(radioController.getStatus(), voiceRelay.voiceStatus(interaction.guild && interaction.guild.id)));
        return;
      }

      if (subcommand === 'skip') {
        await interaction.deferReply({ ephemeral: true });
        const result = await radioController.skipTrack(context);
        await interaction.editReply(resultEmbed('AutoDJ Skip', result));
        return;
      }

      if (subcommand === 'jingle') {
        await interaction.deferReply({ ephemeral: true });
        const name = interaction.options.getString('name', true);
        const result = await radioController.playJingle(name, context);
        await interaction.editReply(resultEmbed('Jingle / ID On-Air', result));
      }
    }

    if (interaction.isButton()) {
      if (!interaction.customId.startsWith('radio:') && !interaction.customId.startsWith('voice:')) return;

      if (!(await guardInteraction(interaction))) return;

      const context = {
        userId: interaction.user.id,
        userTag: interaction.user.tag
      };

      if (interaction.customId === 'radio:skip') {
        await interaction.deferReply({ ephemeral: true });
        const result = await radioController.skipTrack(context);
        await interaction.editReply(resultEmbed('AutoDJ Skip', result));
        return;
      }

      if (interaction.customId === 'radio:status') {
        await interaction.reply(statusEmbed(radioController.getStatus(), voiceRelay.voiceStatus(interaction.guild && interaction.guild.id)));
        return;
      }

      if (interaction.customId === 'voice:play') {
        await interaction.deferReply({ ephemeral: true });
        const result = await voiceRelay.playFromInteraction(interaction, config.voiceRelay.defaultPreset);
        await interaction.editReply(resultEmbed('Voice Stream /play', result));
        return;
      }

      if (interaction.customId.startsWith('voice:preset:')) {
        await interaction.deferReply({ ephemeral: true });
        const preset = interaction.customId.split(':')[2];
        const result = await voiceRelay.playFromInteraction(interaction, preset);
        await interaction.editReply(resultEmbed(`Voice Preset ${preset}`, result));
        return;
      }

      if (interaction.customId === 'voice:pause') {
        await interaction.deferReply({ ephemeral: true });
        const result = await voiceRelay.pauseFromInteraction(interaction);
        await interaction.editReply(resultEmbed('Voice Stream /pause', result));
        return;
      }

      if (interaction.customId === 'voice:resume') {
        await interaction.deferReply({ ephemeral: true });
        const result = await voiceRelay.resumeFromInteraction(interaction);
        await interaction.editReply(resultEmbed('Voice Stream /resume', result));
        return;
      }

      if (interaction.customId === 'voice:stop') {
        await interaction.deferReply({ ephemeral: true });
        const result = await voiceRelay.stopFromInteraction(interaction);
        await interaction.editReply(resultEmbed('Voice Stream /stop', result));
        return;
      }

      if (interaction.customId === 'voice:volume:default') {
        await interaction.deferReply({ ephemeral: true });
        const result = await voiceRelay.resetVolumeFromInteraction(interaction);
        await interaction.editReply(resultEmbed('Voice Default Volume', result));
      }
    }
  } catch (error) {
    logger.error(`Interaction error: ${error.message}`);
    const payload = { content: `Fehler: ${error.message}`, ephemeral: true };
    if (interaction.deferred || interaction.replied) {
      await interaction.editReply(payload).catch(() => null);
    } else {
      await interaction.reply(payload).catch(() => null);
    }
  }
});

client.login(config.discord.token);
