import { EventEmitter } from 'node:events';
import {
  AudioPlayerStatus,
  VoiceConnectionStatus,
  createAudioPlayer,
  createAudioResource,
  entersState,
  getVoiceConnection,
  joinVoiceChannel,
  StreamType
} from '@discordjs/voice';
import prism from 'prism-media';
import ffmpegPath from 'ffmpeg-static';
import { EmbedBuilder } from 'discord.js';
import { IcyMetadataReader } from './icy-metadata-reader.js';
import { StreamHealthMonitor } from './stream-health-monitor.js';

if (ffmpegPath) {
  process.env.FFMPEG_PATH = ffmpegPath;
}

export class RadioCore extends EventEmitter {
  constructor({ client, config, logger }) {
    super();
    this.client = client;
    this.config = config;
    this.logger = logger;
    this.player = createAudioPlayer();
    this.connection = null;
    this.current = null;
    this.reconnectAttempts = 0;
    this.metadataReader = new IcyMetadataReader({ logger });
    this.healthMonitor = new StreamHealthMonitor({
      intervalMs: config.streamHealthIntervalMs,
      timeoutMs: config.streamHealthTimeoutMs,
      logger
    });

    this.bindPlayer();
    this.bindMetadata();
    this.bindHealth();
  }

  bindPlayer() {
    this.player.on(AudioPlayerStatus.Playing, () => {
      this.reconnectAttempts = 0;
      this.logger.info('Radio playback is live.', this.publicStatusFields());
    });

    this.player.on(AudioPlayerStatus.Idle, () => {
      if (this.current && this.config.autoReconnect) {
        this.logger.warn('Audio player became idle while a stream is active. Reconnecting.');
        this.scheduleReconnect('player-idle');
      }
    });

    this.player.on('error', error => {
      this.logger.error('Audio player error.', error, this.publicStatusFields());
      if (this.current && this.config.autoReconnect) this.scheduleReconnect('player-error');
    });
  }

  bindMetadata() {
    this.metadataReader.on('headers', headers => {
      if (headers.stationName && this.current) this.current.stationName ||= headers.stationName;
      this.logger.info('ICY metadata connected.', headers);
    });

    this.metadataReader.on('unavailable', reason => {
      this.logger.warn('ICY metadata unavailable.', { reason });
    });

    this.metadataReader.on('trackChange', event => {
      if (this.current) {
        this.current.currentTrack = event.trackTitle;
        this.current.lastTrackChangeAt = new Date().toISOString();
      }

      this.logger.info('Track change detected.', {
        previous: event.previousTrackTitle || 'UNBEKANNT',
        current: event.trackTitle
      });
      this.emit('trackChange', event);
    });

    this.metadataReader.on('error', error => {
      this.logger.warn('ICY metadata reader error.', { error: error.message });
    });

    this.metadataReader.on('end', () => {
      this.logger.warn('ICY metadata reader ended.');
    });
  }

  bindHealth() {
    this.healthMonitor.on('unhealthy', status => {
      this.logger.warn('Stream health changed to unhealthy.', status);
      if (this.current && this.config.autoReconnect) this.scheduleReconnect('stream-unhealthy');
    });

    this.healthMonitor.on('healthy', status => {
      this.logger.info('Stream health changed to healthy.', status);
    });
  }

  async play({ guild, voiceChannel, streamUrl, stationName, requestedBy }) {
    if (!voiceChannel?.id) {
      throw new Error('Voice channel is missing.');
    }

    const resolvedUrl = streamUrl || this.config.defaultStreamUrl;
    if (!resolvedUrl) {
      throw new Error('No stream URL provided and RADIO_STREAM_URL is not configured.');
    }

    this.assertHttpUrl(resolvedUrl);
    this.stop({ keepConnection: false, reason: 'new-play-request' });

    this.current = {
      guildId: guild.id,
      guildName: guild.name,
      voiceChannelId: voiceChannel.id,
      voiceChannelName: voiceChannel.name,
      adapterCreator: guild.voiceAdapterCreator,
      streamUrl: resolvedUrl,
      stationName: stationName || this.config.defaultStationName,
      requestedBy: requestedBy?.tag || requestedBy?.id || 'UNBEKANNT',
      startedAt: new Date().toISOString(),
      currentTrack: null,
      lastTrackChangeAt: null,
      reconnectReason: null
    };

    await this.connectAndPlay();
    this.healthMonitor.start(resolvedUrl);
    this.metadataReader.start(resolvedUrl);

    return this.snapshot();
  }

  async connectAndPlay() {
    if (!this.current) throw new Error('No active radio stream state.');

    this.connection = joinVoiceChannel({
      channelId: this.current.voiceChannelId,
      guildId: this.current.guildId,
      adapterCreator: this.current.adapterCreator,
      selfDeaf: true
    });

    this.connection.subscribe(this.player);
    this.bindConnection(this.connection);

    await entersState(this.connection, VoiceConnectionStatus.Ready, 20_000);
    this.player.play(this.createFfmpegResource(this.current.streamUrl));
  }

  bindConnection(connection) {
    connection.on(VoiceConnectionStatus.Disconnected, async () => {
      if (!this.current) return;
      this.logger.warn('Voice connection disconnected.', this.publicStatusFields());

      try {
        await Promise.race([
          entersState(connection, VoiceConnectionStatus.Signalling, 5_000),
          entersState(connection, VoiceConnectionStatus.Connecting, 5_000)
        ]);
      } catch {
        connection.destroy();
        if (this.config.autoReconnect) this.scheduleReconnect('voice-disconnected');
      }
    });

    connection.on(VoiceConnectionStatus.Destroyed, () => {
      if (this.current) this.logger.warn('Voice connection destroyed.');
    });
  }

  createFfmpegResource(streamUrl) {
    const ffmpeg = new prism.FFmpeg({
      args: [
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '5',
        '-i', streamUrl,
        '-analyzeduration', '0',
        '-loglevel', '0',
        '-f', 's16le',
        '-ar', '48000',
        '-ac', '2'
      ]
    });

    return createAudioResource(ffmpeg, {
      inputType: StreamType.Raw,
      metadata: {
        title: this.current?.stationName || 'Radio Core'
      }
    });
  }

  scheduleReconnect(reason) {
    if (!this.current) return;

    const max = this.config.maxReconnectAttempts;
    if (max > 0 && this.reconnectAttempts >= max) {
      this.logger.error('Maximum reconnect attempts reached.', null, {
        reason,
        attempts: this.reconnectAttempts
      });
      return;
    }

    this.reconnectAttempts += 1;
    this.current.reconnectReason = reason;
    const delayMs = Math.min(30_000, 2_000 * this.reconnectAttempts);

    setTimeout(async () => {
      if (!this.current) return;
      try {
        this.connection?.destroy();
        await this.connectAndPlay();
        this.metadataReader.start(this.current.streamUrl);
        this.healthMonitor.start(this.current.streamUrl);
      } catch (error) {
        this.logger.error('Reconnect attempt failed.', error, {
          reason,
          attempts: this.reconnectAttempts
        });
        this.scheduleReconnect(reason);
      }
    }, delayMs).unref?.();
  }

  async reconnect(reason = 'manual') {
    if (!this.current) throw new Error('Radio Core is not playing.');
    this.reconnectAttempts = 0;
    this.current.reconnectReason = reason;
    this.connection?.destroy();
    await this.connectAndPlay();
    this.metadataReader.start(this.current.streamUrl);
    this.healthMonitor.start(this.current.streamUrl);
    return this.snapshot();
  }

  stop({ keepConnection = false, reason = 'manual-stop' } = {}) {
    const stopped = this.current;
    this.current = null;
    this.metadataReader.stop();
    this.healthMonitor.stop();
    this.player.stop(true);

    if (!keepConnection) {
      const guildId = stopped?.guildId;
      this.connection?.destroy();
      if (guildId) getVoiceConnection(guildId)?.destroy();
      this.connection = null;
    }

    if (stopped) {
      this.logger.info('Radio playback stopped.', {
        reason,
        stationName: stopped.stationName,
        guildName: stopped.guildName
      });
    }

    this.reconnectAttempts = 0;
  }

  snapshot() {
    return {
      active: Boolean(this.current),
      playerStatus: this.player.state.status,
      connectionStatus: this.connection?.state?.status || null,
      health: this.healthMonitor.snapshot(),
      current: this.current
        ? {
            ...this.current,
            adapterCreator: undefined
          }
        : null,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  publicStatusFields() {
    const snapshot = this.snapshot();
    return {
      active: snapshot.active,
      stationName: snapshot.current?.stationName,
      voiceChannel: snapshot.current?.voiceChannelName,
      playerStatus: snapshot.playerStatus,
      connectionStatus: snapshot.connectionStatus,
      currentTrack: snapshot.current?.currentTrack || 'UNBEKANNT'
    };
  }

  statusEmbed() {
    const snapshot = this.snapshot();
    const embed = new EmbedBuilder()
      .setTitle('666SOUNDsDESIGn Radio Core Status')
      .setColor(snapshot.active ? 0x22c55e : 0x6b7280)
      .setTimestamp(new Date());

    if (!snapshot.active) {
      return embed.setDescription('Radio Core ist aktuell nicht verbunden.');
    }

    embed.setDescription(snapshot.current.stationName);
    embed.addFields(
      { name: 'Voice Channel', value: snapshot.current.voiceChannelName || 'UNBEKANNT', inline: true },
      { name: 'Playback', value: snapshot.playerStatus || 'UNBEKANNT', inline: true },
      { name: 'Connection', value: snapshot.connectionStatus || 'UNBEKANNT', inline: true },
      { name: 'Track', value: snapshot.current.currentTrack || 'UNBEKANNT', inline: false },
      {
        name: 'Health',
        value: snapshot.health.healthy
          ? `OK (${snapshot.health.statusCode || 'UNBEKANNT'})`
          : `Problem: ${snapshot.health.error || 'UNBEKANNT'}`,
        inline: true
      },
      { name: 'Reconnects', value: String(snapshot.reconnectAttempts), inline: true }
    );

    return embed;
  }

  assertHttpUrl(value) {
    let url;
    try {
      url = new URL(value);
    } catch {
      throw new Error('Stream URL is invalid.');
    }

    if (!['http:', 'https:'].includes(url.protocol)) {
      throw new Error('Only http(s) stream URLs are supported.');
    }
  }
}
