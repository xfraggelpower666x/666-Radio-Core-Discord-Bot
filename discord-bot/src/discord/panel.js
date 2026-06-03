/**
 * 666RadioCoreDJ | src/discord/panel.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Discord-Control-Panel mit Buttons für schnelle Radio- und Voice-Aktionen.
 * Änderung v1.3.0: Preset-Buttons 1-5, Pause/Resume und Default-Volume ergänzt.
 */
const {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  EmbedBuilder
} = require('discord.js');

function presetLabel(config, index) {
  const preset = (config.voiceRelay.presets || [])[index - 1];
  if (!preset) return `Preset ${index}`;
  return preset.url ? `${index}: ${preset.name}` : `${index}: leer`;
}

function buildControlPanel(config) {
  const configuredPresets = (config.voiceRelay.presets || []).filter((preset) => Boolean(preset.url)).length;
  const embed = new EmbedBuilder()
    .setTitle(config.app.controlPanelTitle)
    .setDescription('SonicPanel/MyIDJ AutoDJ-Steuerung und Discord-Voice-Stream über den 666RadioCoreDJ Service-Account.')
    .addFields(
      { name: 'Primary', value: config.radioControl.primary || 'disabled', inline: true },
      { name: 'Fallback', value: config.radioControl.fallback || 'disabled', inline: true },
      { name: 'Version', value: config.app.version, inline: true },
      { name: 'Voice Default', value: `Preset ${config.voiceRelay.defaultPreset} / ${config.voiceRelay.defaultVolumePercent}%`, inline: true },
      { name: 'Presets', value: `${configuredPresets}/5 konfiguriert`, inline: true },
      { name: 'Voice Stream', value: config.voiceRelay.streamUrl || configuredPresets ? 'konfiguriert' : 'Stream fehlt', inline: true }
    )
    .setFooter({ text: 'Keine Secrets in Discord. Zugriff nur über Rollen/Channel-Gate.' });

  const radioRow = new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId('radio:skip')
      .setLabel('AutoDJ Skip')
      .setEmoji('⏭️')
      .setStyle(ButtonStyle.Danger),
    new ButtonBuilder()
      .setCustomId('radio:status')
      .setLabel('Status')
      .setEmoji('📡')
      .setStyle(ButtonStyle.Secondary)
  );

  const voiceRow = new ActionRowBuilder().addComponents(
    new ButtonBuilder()
      .setCustomId('voice:play')
      .setLabel('Play Default')
      .setEmoji('▶️')
      .setStyle(ButtonStyle.Success),
    new ButtonBuilder()
      .setCustomId('voice:pause')
      .setLabel('Pause')
      .setEmoji('⏸️')
      .setStyle(ButtonStyle.Secondary),
    new ButtonBuilder()
      .setCustomId('voice:resume')
      .setLabel('Resume')
      .setEmoji('▶️')
      .setStyle(ButtonStyle.Primary),
    new ButtonBuilder()
      .setCustomId('voice:stop')
      .setLabel('Stop')
      .setEmoji('⏹️')
      .setStyle(ButtonStyle.Secondary),
    new ButtonBuilder()
      .setCustomId('voice:volume:default')
      .setLabel('Vol Default')
      .setEmoji('🔊')
      .setStyle(ButtonStyle.Secondary)
  );

  const presetRow = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId('voice:preset:1').setLabel(presetLabel(config, 1)).setStyle(ButtonStyle.Secondary),
    new ButtonBuilder().setCustomId('voice:preset:2').setLabel(presetLabel(config, 2)).setStyle(ButtonStyle.Secondary),
    new ButtonBuilder().setCustomId('voice:preset:3').setLabel(presetLabel(config, 3)).setStyle(ButtonStyle.Secondary),
    new ButtonBuilder().setCustomId('voice:preset:4').setLabel(presetLabel(config, 4)).setStyle(ButtonStyle.Secondary),
    new ButtonBuilder().setCustomId('voice:preset:5').setLabel(presetLabel(config, 5)).setStyle(ButtonStyle.Secondary)
  );

  return { embeds: [embed], components: [radioRow, voiceRow, presetRow] };
}

module.exports = { buildControlPanel };
