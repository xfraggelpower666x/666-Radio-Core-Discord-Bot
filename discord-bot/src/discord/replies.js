/**
 * 666RadioCoreDJ | src/discord/replies.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Einheitliche Discord-Antworten ohne Secret-Leaks.
 * Änderung v1.3.0: Preset-, Pause- und Volume-Statusfelder ergänzt.
 */
const { EmbedBuilder } = require('discord.js');
const { redact } = require('../utils/redact');

function resultEmbed(title, result) {
  const embed = new EmbedBuilder()
    .setTitle(title)
    .setDescription(redact(result.message || 'Keine Detailmeldung.'))
    .addFields(
      { name: 'Status', value: result.ok ? 'OK' : 'FEHLER', inline: true },
      { name: 'Code', value: redact(result.code || 'UNKNOWN'), inline: true },
      { name: 'Adapter', value: redact(result.adapter || 'core'), inline: true }
    );

  if (result.status) {
    embed.addFields({ name: 'HTTP', value: String(result.status), inline: true });
  }

  if (result.channelName) {
    embed.addFields({ name: 'Voice Channel', value: redact(result.channelName), inline: true });
  }

  if (result.presetName) {
    embed.addFields({ name: 'Preset', value: redact(result.presetName), inline: true });
  }

  if (typeof result.volumePercent === 'number') {
    embed.addFields({ name: 'Volume', value: `${result.volumePercent}%`, inline: true });
  }

  if (result.primaryFailed && result.primaryFailed.code) {
    embed.addFields({ name: 'Primary fehlgeschlagen', value: redact(result.primaryFailed.code), inline: true });
  }

  return { embeds: [embed], ephemeral: true };
}

function statusEmbed(status, voiceStatus = {}) {
  const health = voiceStatus.streamHealth;
  const healthText = health
    ? (health.healthy ? `OK (${health.statusCode || 'UNBEKANNT'})` : `Problem: ${redact(health.error || 'UNBEKANNT')}`)
    : 'UNBEKANNT';

  const embed = new EmbedBuilder()
    .setTitle('666RadioCoreDJ Status')
    .addFields(
      { name: 'Version', value: status.version, inline: true },
      { name: 'Primary', value: status.primary, inline: true },
      { name: 'Fallback', value: status.fallback, inline: true },
      { name: 'SonicPanel Skip URL', value: status.sonicPanelConfigured ? 'konfiguriert' : 'fehlt', inline: true },
      { name: 'Jingle URL', value: status.jingleConfigured ? 'konfiguriert' : 'fehlt', inline: true },
      { name: 'SHOUTcast Fallback', value: status.shoutcastFallbackConfigured ? 'konfiguriert' : 'fehlt/deaktiviert', inline: true },
      { name: 'Voice Auto-Relay', value: status.voiceRelayEnabled ? 'aktiv' : 'deaktiviert', inline: true },
      { name: 'Voice Stream', value: status.voiceStreamConfigured ? 'konfiguriert' : 'Stream fehlt', inline: true },
      { name: 'Presets', value: `${status.voicePresetCount || 0}/5`, inline: true },
      { name: 'Default', value: `Preset ${status.voiceDefaultPreset || '1'} / ${status.voiceDefaultVolumePercent || 80}%`, inline: true },
      { name: 'Aktiv', value: voiceStatus.active ? `${voiceStatus.paused ? 'pausiert' : 'läuft'} in ${redact(voiceStatus.channelName)}` : 'nein', inline: true },
      { name: 'Aktuelle Lautstärke', value: `${voiceStatus.volumePercent || status.voiceDefaultVolumePercent || 80}%`, inline: true },
      { name: 'Broadcast Status', value: healthText, inline: true },
      { name: 'Station', value: redact(voiceStatus.stationName || voiceStatus.presetName || 'UNBEKANNT'), inline: true },
      { name: 'Track', value: redact(voiceStatus.currentTrack || 'UNBEKANNT'), inline: false }
    );

  return { embeds: [embed], ephemeral: true };
}

module.exports = { resultEmbed, statusEmbed };
