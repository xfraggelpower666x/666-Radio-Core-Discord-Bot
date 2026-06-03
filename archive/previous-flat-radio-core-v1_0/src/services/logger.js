import { EmbedBuilder } from 'discord.js';

export class BotLogger {
  constructor({ client, logChannelId = null }) {
    this.client = client;
    this.logChannelId = logChannelId;
  }

  info(message, details = {}) {
    console.log(`[info] ${message}`, details);
    return this.sendLog('Info', message, details, 0x2f80ed);
  }

  warn(message, details = {}) {
    console.warn(`[warn] ${message}`, details);
    return this.sendLog('Warnung', message, details, 0xf59e0b);
  }

  error(message, error = null, details = {}) {
    const payload = {
      ...details,
      error: error?.message || error || undefined
    };
    console.error(`[error] ${message}`, payload);
    return this.sendLog('Fehler', message, payload, 0xef4444);
  }

  async sendLog(title, message, details, color) {
    if (!this.logChannelId || !this.client?.isReady?.()) return;

    try {
      const channel = await this.client.channels.fetch(this.logChannelId);
      if (!channel?.isTextBased?.()) return;

      const embed = new EmbedBuilder()
        .setTitle(`Radio Core ${title}`)
        .setDescription(message)
        .setColor(color)
        .setTimestamp(new Date());

      const fields = Object.entries(details || {})
        .filter(([, value]) => value !== undefined && value !== null && value !== '')
        .slice(0, 8)
        .map(([name, value]) => ({
          name,
          value: String(value).slice(0, 1024),
          inline: true
        }));

      if (fields.length > 0) embed.addFields(fields);
      await channel.send({ embeds: [embed] });
    } catch (error) {
      console.warn('[warn] Log channel delivery failed', error.message);
    }
  }
}
