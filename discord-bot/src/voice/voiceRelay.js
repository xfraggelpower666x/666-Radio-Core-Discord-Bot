/**
 * 666RadioCoreDJ | src/voice/voiceRelay.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Discord-Voice-Stream für Radiostreams mit Presets, Pause/Resume, Stop und Lautstärkesteuerung.
 * Änderung v1.3.0: 5 Stream-Presets, /pause, /resume, /volume, Default-Volume und Panel-Preset-Starts ergänzt.
 */
const { spawn } = require('child_process');
const ffmpegStatic = require('ffmpeg-static');
const {
  AudioPlayerStatus,
  createAudioPlayer,
  createAudioResource,
  entersState,
  joinVoiceChannel,
  NoSubscriberBehavior,
  StreamType,
  VoiceConnectionStatus
} = require('@discordjs/voice');
const { PermissionsBitField } = require('discord.js');
const logger = require('../utils/logger');
const { redact } = require('../utils/redact');
const { IcyMetadataReader } = require('../radio/icyMetadataReader');
const { StreamHealthMonitor } = require('../radio/streamHealthMonitor');

function seconds(value, fallback) {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function percentToVolume(percent) {
  return clamp(Number(percent) || 0, 0, 200) / 100;
}

function normalizeKey(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-');
}

function ffmpegBinary() {
  return ffmpegStatic || process.env.FFMPEG_PATH || 'ffmpeg';
}

function isHttpUrl(value) {
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol);
  } catch {
    return false;
  }
}

function createFfmpegPcmStream(streamUrl) {
  const args = [
    '-hide_banner',
    '-loglevel', 'warning',
    '-reconnect', '1',
    '-reconnect_streamed', '1',
    '-reconnect_delay_max', '5',
    '-i', streamUrl,
    '-vn',
    '-f', 's16le',
    '-ar', '48000',
    '-ac', '2',
    'pipe:1'
  ];

  const processRef = spawn(ffmpegBinary(), args, {
    windowsHide: true,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  processRef.stderr.on('data', (chunk) => {
    const line = redact(chunk.toString('utf8').trim());
    if (line) logger.warn(`FFmpeg: ${line}`);
  });

  processRef.on('error', (error) => {
    logger.error(`FFmpeg process error: ${error.message}`);
  });

  return processRef;
}

class VoiceRelayManager {
  constructor(config) {
    this.config = config;
    this.states = new Map();
    this.reconnectSeconds = seconds(config.voiceRelay.reconnectSeconds, 10);
    this.healthIntervalSeconds = seconds(config.voiceRelay.healthIntervalSeconds, 30);
    this.healthTimeoutSeconds = seconds(config.voiceRelay.healthTimeoutSeconds, 10);
    this.defaultVolumePercent = clamp(config.voiceRelay.defaultVolumePercent, 0, config.voiceRelay.maxVolumePercent || 200);
    this.maxVolumePercent = clamp(config.voiceRelay.maxVolumePercent || 200, 1, 200);
  }

  fallbackStreamUrl() {
    return this.config.voiceRelay.streamUrl;
  }

  configuredPresets() {
    return this.config.voiceRelay.presets.filter((preset) => Boolean(preset.url));
  }

  presetByInput(input) {
    const value = normalizeKey(input || this.config.voiceRelay.defaultPreset || '1');
    const presets = this.config.voiceRelay.presets || [];

    const direct = presets.find((preset) => normalizeKey(preset.id) === value || normalizeKey(preset.name) === value);
    if (direct && direct.url) return direct;

    const firstConfigured = presets.find((preset) => Boolean(preset.url));
    if (firstConfigured) return firstConfigured;

    if (this.fallbackStreamUrl()) {
      return {
        id: 'fallback',
        name: 'RADIO_STREAM_URL',
        url: this.fallbackStreamUrl(),
        volumePercent: null
      };
    }

    return null;
  }

  voiceStatus(guildId) {
    const state = guildId ? this.states.get(guildId) : null;
    return {
      active: Boolean(state),
      paused: Boolean(state && state.paused),
      channelName: state ? state.channelName : '',
      presetName: state && state.preset ? state.preset.name : '',
      presetId: state && state.preset ? state.preset.id : '',
      volumePercent: state ? Math.round(state.volumePercent) : this.defaultVolumePercent,
      stationName: state && state.stationName ? state.stationName : '',
      currentTrack: state && state.currentTrack ? state.currentTrack : '',
      lastTrackChangeAt: state && state.lastTrackChangeAt ? state.lastTrackChangeAt : '',
      streamHealth: state && state.streamHealth ? { ...state.streamHealth } : null,
      configuredPresets: this.configuredPresets().length,
      defaultVolumePercent: this.defaultVolumePercent,
      maxVolumePercent: this.maxVolumePercent
    };
  }

  validateVoiceChannel(channel, clientUser) {
    if (!channel || !channel.guild) {
      return { ok: false, code: 'VOICE_CHANNEL_MISSING', message: 'Du musst zuerst in einem Voice-Channel sein.' };
    }

    const permissions = channel.permissionsFor(clientUser);
    if (!permissions || !permissions.has(PermissionsBitField.Flags.Connect)) {
      return { ok: false, code: 'VOICE_CONNECT_DENIED', message: 'Der Bot darf diesem Voice-Channel nicht beitreten.' };
    }

    if (!permissions.has(PermissionsBitField.Flags.Speak)) {
      return { ok: false, code: 'VOICE_SPEAK_DENIED', message: 'Der Bot darf in diesem Voice-Channel nicht sprechen/streamen.' };
    }

    return { ok: true };
  }

  async playFromInteraction(interaction, presetInput = null) {
    if (!interaction.guild || !interaction.member) {
      return { ok: false, code: 'GUILD_ONLY', adapter: 'voice', message: '/play funktioniert nur auf einem Discord-Server.' };
    }

    const channel = interaction.member.voice && interaction.member.voice.channel;
    if (!channel) {
      return { ok: false, code: 'USER_NOT_IN_VOICE', adapter: 'voice', message: 'Geh zuerst in einen Voice-Channel und nutze dann /play.' };
    }

    return this.playInChannel(channel, {
      userId: interaction.user.id,
      userTag: interaction.user.tag,
      source: '/play',
      presetInput
    });
  }

  async playInChannel(channel, context = {}) {
    const preset = this.presetByInput(context.presetInput);
    if (!preset || !preset.url) {
      return {
        ok: false,
        code: 'STREAM_URL_MISSING',
        adapter: 'voice',
        message: 'Kein Stream konfiguriert. Setze RADIO_STREAM_URL oder STREAM_PRESET_1_URL bis STREAM_PRESET_5_URL in .env.'
      };
    }

    if (!isHttpUrl(preset.url)) {
      return {
        ok: false,
        code: 'STREAM_URL_INVALID',
        adapter: 'voice',
        message: 'Stream-URL ist ungueltig. Fuer SHOUTcast/Icecast werden http(s)-URLs erwartet.'
      };
    }

    const validation = this.validateVoiceChannel(channel, channel.client.user);
    if (!validation.ok) return { ...validation, adapter: 'voice' };

    await this.stopGuild(channel.guild.id, false);

    const presetVolume = preset.volumePercent || this.defaultVolumePercent;
    const volumePercent = clamp(presetVolume, 0, this.maxVolumePercent);

    logger.info('Starting voice stream', {
      guildId: channel.guild.id,
      channelId: channel.id,
      channelName: channel.name,
      presetId: preset.id,
      presetName: preset.name,
      volumePercent,
      userId: context.userId,
      userTag: context.userTag,
      source: context.source || 'manual'
    });

    const connection = joinVoiceChannel({
      channelId: channel.id,
      guildId: channel.guild.id,
      adapterCreator: channel.guild.voiceAdapterCreator,
      selfDeaf: true
    });

    await entersState(connection, VoiceConnectionStatus.Ready, 30000);

    const player = createAudioPlayer({
      behaviors: {
        noSubscriber: NoSubscriberBehavior.Play
      }
    });

    connection.subscribe(player);

    const state = {
      guildId: channel.guild.id,
      channelId: channel.id,
      channelName: channel.name,
      client: channel.client,
      connection,
      player,
      ffmpeg: null,
      resource: null,
      manualStop: false,
      paused: false,
      restartTimer: null,
      context,
      preset,
      streamUrl: preset.url,
      volumePercent,
      metadataReader: new IcyMetadataReader({ logger }),
      healthMonitor: new StreamHealthMonitor({
        intervalMs: this.healthIntervalSeconds * 1000,
        timeoutMs: this.healthTimeoutSeconds * 1000,
        logger
      }),
      stationName: '',
      currentTrack: '',
      lastTrackChangeAt: '',
      streamHealth: null
    };

    this.states.set(channel.guild.id, state);
    this.attachStateEvents(state);
    this.attachStreamObservability(state);
    this.startStreamForState(state);
    this.startStreamObservability(state);

    return {
      ok: true,
      code: 'VOICE_STREAM_STARTED',
      adapter: 'voice',
      channelName: channel.name,
      presetName: preset.name,
      volumePercent,
      message: `Radiostream „${preset.name}“ wurde in „${channel.name}“ gestartet. Lautstärke: ${volumePercent}%.`
    };
  }

  attachStateEvents(state) {
    state.player.on(AudioPlayerStatus.Idle, () => {
      if (state.manualStop || state.paused) return;
      logger.warn('Voice stream became idle. Scheduling restart.', { guildId: state.guildId });
      this.scheduleRestart(state);
    });

    state.player.on('error', (error) => {
      if (state.manualStop || state.paused) return;
      logger.error(`Voice player error: ${error.message}`);
      this.scheduleRestart(state);
    });

    state.connection.on(VoiceConnectionStatus.Disconnected, async () => {
      if (state.manualStop) return;
      logger.warn('Voice connection disconnected.', { guildId: state.guildId });
      this.scheduleRestart(state);
    });

    state.connection.on(VoiceConnectionStatus.Destroyed, () => {
      this.cleanupState(state);
    });
  }

  attachStreamObservability(state) {
    state.metadataReader.on('headers', (headers) => {
      if (headers.stationName) state.stationName = headers.stationName;
      logger.info('ICY metadata connected.', {
        guildId: state.guildId,
        stationName: headers.stationName || 'UNBEKANNT',
        statusCode: headers.statusCode,
        contentType: headers.contentType,
        metadataInterval: headers.metadataInterval
      });
    });

    state.metadataReader.on('unavailable', (reason) => {
      logger.warn('ICY metadata unavailable.', { guildId: state.guildId, reason });
    });

    state.metadataReader.on('trackChange', (event) => {
      state.currentTrack = event.trackTitle;
      state.lastTrackChangeAt = new Date().toISOString();
      logger.info('Track change detected.', {
        guildId: state.guildId,
        previous: event.previousTrackTitle || 'UNBEKANNT',
        current: event.trackTitle
      });
      this.sendLogMessage(state, 'Track Change', `Jetzt laeuft: ${event.trackTitle}`);
    });

    state.metadataReader.on('error', (error) => {
      logger.warn('ICY metadata reader error.', { guildId: state.guildId, error: error.message });
    });

    state.metadataReader.on('end', () => {
      logger.warn('ICY metadata reader ended.', { guildId: state.guildId });
    });

    state.healthMonitor.on('status', (status) => {
      state.streamHealth = status;
    });

    state.healthMonitor.on('healthy', (status) => {
      logger.info('Stream health changed to healthy.', { guildId: state.guildId, statusCode: status.statusCode });
      this.sendLogMessage(state, 'Stream Health', `OK (${status.statusCode || 'UNBEKANNT'})`);
    });

    state.healthMonitor.on('unhealthy', (status) => {
      logger.warn('Stream health changed to unhealthy.', { guildId: state.guildId, error: status.error });
      this.sendLogMessage(state, 'Stream Health', `Problem: ${status.error || 'UNBEKANNT'}`);
      this.scheduleRestart(state);
    });
  }

  startStreamObservability(state) {
    if (!state || state.manualStop || state.paused) return;
    state.metadataReader.start(state.streamUrl);
    state.healthMonitor.start(state.streamUrl);
  }

  stopStreamObservability(state) {
    if (!state) return;
    state.metadataReader.stop();
    state.healthMonitor.stop();
  }

  async sendLogMessage(state, title, message) {
    const channelId = this.config.discord.logChannelId;
    if (!channelId || !state || !state.client) return;

    try {
      const channel = await state.client.channels.fetch(channelId);
      if (channel && channel.send) {
        await channel.send(`**666RadioCoreDJ ${redact(title)}**\n${redact(message)}`);
      }
    } catch (error) {
      logger.warn('Log channel message could not be sent.', { guildId: state.guildId, error: error.message });
    }
  }

  startStreamForState(state) {
    if (state.manualStop || state.paused) return;

    this.killFfmpeg(state);

    try {
      const ffmpeg = createFfmpegPcmStream(state.streamUrl);
      state.ffmpeg = ffmpeg;

      ffmpeg.on('exit', (code, signal) => {
        if (state.manualStop || state.paused) return;
        logger.warn('FFmpeg exited. Scheduling stream restart.', { code, signal, guildId: state.guildId });
        this.scheduleRestart(state);
      });

      const resource = createAudioResource(ffmpeg.stdout, {
        inputType: StreamType.Raw,
        inlineVolume: true
      });

      state.resource = resource;
      if (resource.volume) resource.volume.setVolume(percentToVolume(state.volumePercent));
      state.player.play(resource);
    } catch (error) {
      logger.error(`Voice stream start failed: ${error.message}`);
      this.scheduleRestart(state);
    }
  }

  scheduleRestart(state) {
    if (state.manualStop || state.paused || state.restartTimer) return;

    state.restartTimer = setTimeout(() => {
      state.restartTimer = null;
      if (!state.manualStop && !state.paused && this.states.get(state.guildId) === state) {
        this.startStreamForState(state);
        this.startStreamObservability(state);
      }
    }, this.reconnectSeconds * 1000);
  }

  killFfmpeg(state) {
    if (!state || !state.ffmpeg) return;

    const ffmpeg = state.ffmpeg;
    state.ffmpeg = null;

    try {
      if (!ffmpeg.killed) ffmpeg.kill('SIGKILL');
    } catch (error) {
      logger.warn(`Could not kill FFmpeg: ${error.message}`);
    }
  }

  cleanupState(state) {
    if (!state) return;
    if (state.restartTimer) {
      clearTimeout(state.restartTimer);
      state.restartTimer = null;
    }
    this.killFfmpeg(state);
    state.resource = null;
    this.stopStreamObservability(state);
  }

  activeStateOrError(guildId, commandName) {
    const state = this.states.get(guildId);
    if (!state) {
      return {
        state: null,
        result: {
          ok: false,
          code: 'VOICE_NOT_ACTIVE',
          adapter: 'voice',
          message: `${commandName} kann nicht ausgeführt werden, weil auf diesem Server kein Voice-Stream läuft.`
        }
      };
    }

    return { state, result: null };
  }

  async pauseFromInteraction(interaction) {
    if (!interaction.guild) {
      return { ok: false, code: 'GUILD_ONLY', adapter: 'voice', message: '/pause funktioniert nur auf einem Discord-Server.' };
    }

    const { state, result } = this.activeStateOrError(interaction.guild.id, '/pause');
    if (!state) return result;

    if (state.paused) {
      return { ok: true, code: 'VOICE_ALREADY_PAUSED', adapter: 'voice', channelName: state.channelName, message: 'Der Voice-Stream ist bereits pausiert.' };
    }

    state.paused = true;
    this.cleanupState(state);
    try {
      state.player.stop(true);
    } catch (error) {
      logger.warn(`Player pause warning: ${error.message}`);
    }

    return {
      ok: true,
      code: 'VOICE_STREAM_PAUSED',
      adapter: 'voice',
      channelName: state.channelName,
      presetName: state.preset.name,
      volumePercent: state.volumePercent,
      message: `Voice-Stream „${state.preset.name}“ ist pausiert. Der Bot bleibt in „${state.channelName}“. Mit /resume geht es live weiter.`
    };
  }

  async resumeFromInteraction(interaction) {
    if (!interaction.guild) {
      return { ok: false, code: 'GUILD_ONLY', adapter: 'voice', message: '/resume funktioniert nur auf einem Discord-Server.' };
    }

    const { state, result } = this.activeStateOrError(interaction.guild.id, '/resume');
    if (!state) return result;

    if (!state.paused) {
      return { ok: true, code: 'VOICE_NOT_PAUSED', adapter: 'voice', channelName: state.channelName, message: 'Der Voice-Stream ist nicht pausiert.' };
    }

    state.paused = false;
    this.startStreamForState(state);
    this.startStreamObservability(state);

    return {
      ok: true,
      code: 'VOICE_STREAM_RESUMED',
      adapter: 'voice',
      channelName: state.channelName,
      presetName: state.preset.name,
      volumePercent: state.volumePercent,
      message: `Voice-Stream „${state.preset.name}“ läuft wieder live in „${state.channelName}“. Lautstärke: ${state.volumePercent}%.`
    };
  }

  async setVolumeFromInteraction(interaction) {
    if (!interaction.guild) {
      return { ok: false, code: 'GUILD_ONLY', adapter: 'voice', message: '/volume funktioniert nur auf einem Discord-Server.' };
    }

    const { state, result } = this.activeStateOrError(interaction.guild.id, '/volume');
    if (!state) return result;

    const useDefault = interaction.options.getBoolean('default') === true;
    const requested = interaction.options.getInteger('level');

    if (!useDefault && requested === null) {
      return {
        ok: true,
        code: 'VOICE_VOLUME_STATUS',
        adapter: 'voice',
        channelName: state.channelName,
        presetName: state.preset.name,
        volumePercent: state.volumePercent,
        message: `Aktuelle Voice-Lautstärke: ${state.volumePercent}%. Default: ${this.defaultVolumePercent}%. Max: ${this.maxVolumePercent}%.`
      };
    }

    const nextVolume = useDefault
      ? this.defaultVolumePercent
      : clamp(requested, 0, this.maxVolumePercent);

    state.volumePercent = nextVolume;
    if (state.resource && state.resource.volume) {
      state.resource.volume.setVolume(percentToVolume(nextVolume));
    }

    return {
      ok: true,
      code: useDefault ? 'VOICE_VOLUME_DEFAULT' : 'VOICE_VOLUME_SET',
      adapter: 'voice',
      channelName: state.channelName,
      presetName: state.preset.name,
      volumePercent: state.volumePercent,
      message: `Voice-Lautstärke gesetzt: ${state.volumePercent}%.`
    };
  }

  async resetVolumeFromInteraction(interaction) {
    if (!interaction.guild) {
      return { ok: false, code: 'GUILD_ONLY', adapter: 'voice', message: 'Default-Lautstärke funktioniert nur auf einem Discord-Server.' };
    }

    const { state, result } = this.activeStateOrError(interaction.guild.id, 'Default-Lautstärke');
    if (!state) return result;

    state.volumePercent = this.defaultVolumePercent;
    if (state.resource && state.resource.volume) {
      state.resource.volume.setVolume(percentToVolume(state.volumePercent));
    }

    return {
      ok: true,
      code: 'VOICE_VOLUME_DEFAULT',
      adapter: 'voice',
      channelName: state.channelName,
      presetName: state.preset.name,
      volumePercent: state.volumePercent,
      message: `Voice-Lautstärke wurde auf Default gesetzt: ${state.volumePercent}%.`
    };
  }

  async stopGuild(guildId, reportIfMissing = true) {
    const state = this.states.get(guildId);
    if (!state) {
      return reportIfMissing
        ? { ok: false, code: 'VOICE_NOT_ACTIVE', adapter: 'voice', message: 'Der Voice-Stream läuft auf diesem Server gerade nicht.' }
        : { ok: true, code: 'VOICE_NOT_ACTIVE', adapter: 'voice', message: 'Kein aktiver Voice-Stream vorhanden.' };
    }

    logger.info('Stopping voice stream', { guildId, channelId: state.channelId });
    state.manualStop = true;
    this.cleanupState(state);

    try {
      state.player.stop(true);
    } catch (error) {
      logger.warn(`Player stop warning: ${error.message}`);
    }

    try {
      state.connection.destroy();
    } catch (error) {
      logger.warn(`Connection destroy warning: ${error.message}`);
    }

    this.states.delete(guildId);

    return {
      ok: true,
      code: 'VOICE_STREAM_STOPPED',
      adapter: 'voice',
      channelName: state.channelName,
      presetName: state.preset ? state.preset.name : '',
      volumePercent: state.volumePercent,
      message: `Radiostream wurde aus „${state.channelName}“ getrennt.`
    };
  }

  async stopFromInteraction(interaction) {
    if (!interaction.guild) {
      return { ok: false, code: 'GUILD_ONLY', adapter: 'voice', message: '/stop funktioniert nur auf einem Discord-Server.' };
    }

    return this.stopGuild(interaction.guild.id, true);
  }

  async startAutoRelay(client) {
    if (!this.config.voiceRelay.enabled) return;

    const preset = this.presetByInput(this.config.voiceRelay.defaultPreset);
    if (!this.config.voiceRelay.channelId || !preset || !preset.url) {
      logger.warn('Voice auto-relay enabled, but VOICE_CHANNEL_ID or stream preset/RADIO_STREAM_URL is missing.');
      return;
    }

    const channel = await client.channels.fetch(this.config.voiceRelay.channelId);
    if (!channel || !channel.guild) {
      logger.warn('Voice auto-relay channel not found.');
      return;
    }

    const result = await this.playInChannel(channel, { source: 'auto-relay', presetInput: this.config.voiceRelay.defaultPreset });
    if (!result.ok) logger.warn('Voice auto-relay failed', result);
  }
}

async function startVoiceRelay(client, config) {
  const manager = new VoiceRelayManager(config);
  await manager.startAutoRelay(client);
  return manager;
}

module.exports = { VoiceRelayManager, startVoiceRelay };
