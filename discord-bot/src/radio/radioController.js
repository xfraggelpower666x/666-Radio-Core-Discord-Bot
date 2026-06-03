/**
 * 666RadioCoreDJ | src/radio/radioController.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Zentrale Radio-Control-Logik mit Primary/Fallback-Adapter, Cooldown und Audit-freundlichen Ergebnissen.
 * Änderung v1.3.0: Status um 5 Voice-Stream-Presets und Default-Volume erweitert.
 */
const { SonicPanelAdapter } = require('./adapters/sonicPanelAdapter');
const { ShoutcastAdapter } = require('./adapters/shoutcastAdapter');
const logger = require('../utils/logger');

class RadioController {
  constructor(config) {
    this.config = config;
    this.sonicPanel = new SonicPanelAdapter(config.sonicPanel);
    this.shoutcast = new ShoutcastAdapter(config.shoutcast);
    this.cooldowns = new Map();
  }

  cooldownKey(action, userId) {
    return `${action}:${userId}`;
  }

  checkCooldown(action, userId, seconds) {
    const key = this.cooldownKey(action, userId);
    const now = Date.now();
    const until = this.cooldowns.get(key) || 0;

    if (until > now) {
      return Math.ceil((until - now) / 1000);
    }

    this.cooldowns.set(key, now + seconds * 1000);
    return 0;
  }

  async skipTrack(context = {}) {
    const remaining = this.checkCooldown('skip', context.userId || 'unknown', this.config.cooldowns.skipSeconds);
    if (remaining > 0) {
      return {
        ok: false,
        code: 'COOLDOWN_ACTIVE',
        message: `Skip-Cooldown aktiv. Bitte noch ${remaining}s warten.`
      };
    }

    logger.info('Radio skip requested', { userId: context.userId, userTag: context.userTag });

    let primaryResult = { ok: false, code: 'PRIMARY_DISABLED', message: 'Primary Skip-Adapter ist deaktiviert.' };

    if (this.config.radioControl.primary === 'direct_sonicpanel') {
      primaryResult = await this.sonicPanel.skipTrack();
    }

    if (primaryResult.ok) return primaryResult;

    logger.warn('Primary skip failed', primaryResult);

    if (this.config.radioControl.fallback === 'shoutcast_kicksrc') {
      const fallbackResult = await this.shoutcast.kickSource();
      return {
        ...fallbackResult,
        primaryFailed: primaryResult
      };
    }

    return primaryResult;
  }

  async playJingle(nameOrId, context = {}) {
    const remaining = this.checkCooldown('jingle', context.userId || 'unknown', this.config.cooldowns.jingleSeconds);
    if (remaining > 0) {
      return {
        ok: false,
        code: 'COOLDOWN_ACTIVE',
        message: `Jingle-Cooldown aktiv. Bitte noch ${remaining}s warten.`
      };
    }

    logger.info('Radio jingle requested', { userId: context.userId, userTag: context.userTag, nameOrId });
    return this.sonicPanel.playJingle(nameOrId);
  }

  getStatus() {
    return {
      name: this.config.app.name,
      version: this.config.app.version,
      primary: this.config.radioControl.primary,
      fallback: this.config.radioControl.fallback,
      sonicPanelConfigured: Boolean(this.config.sonicPanel.skipUrl),
      jingleConfigured: Boolean(this.config.sonicPanel.jingleUrlTemplate),
      shoutcastFallbackConfigured: Boolean(this.config.shoutcast.adminCgiUrl && this.config.shoutcast.adminPass),
      voiceRelayEnabled: this.config.voiceRelay.enabled,
      voiceStreamConfigured: Boolean(this.config.voiceRelay.streamUrl || this.config.voiceRelay.presets.some((preset) => Boolean(preset.url))),
      voicePresetCount: this.config.voiceRelay.presets.filter((preset) => Boolean(preset.url)).length,
      voiceDefaultPreset: this.config.voiceRelay.defaultPreset,
      voiceDefaultVolumePercent: this.config.voiceRelay.defaultVolumePercent
    };
  }
}

module.exports = { RadioController };
