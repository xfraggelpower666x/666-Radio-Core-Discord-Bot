/**
 * 666RadioCoreDJ | src/radio/icyMetadataReader.js
 * Zweck: ICY-Metadaten von SHOUTcast/Icecast-Streams lesen und Track-Wechsel erkennen.
 */
const { EventEmitter } = require('events');
const http = require('http');
const https = require('https');
const { parseIcyMetadata, normalizeTrackTitle } = require('../utils/track');

const USER_AGENT = '666-Radio-Core-Discord-Bot/1.3';

class IcyMetadataReader extends EventEmitter {
  constructor({ logger: readerLogger = null } = {}) {
    super();
    this.logger = readerLogger;
    this.request = null;
    this.response = null;
    this.active = false;
    this.lastTrackTitle = null;
  }

  start(streamUrl) {
    this.stop();
    this.active = true;

    let url;
    try {
      url = new URL(streamUrl);
    } catch (error) {
      this.emit('error', new Error(`Invalid stream URL for ICY metadata: ${error.message}`));
      return;
    }

    const transport = url.protocol === 'https:' ? https : http;
    this.request = transport.get(
      url,
      {
        headers: {
          'Icy-MetaData': '1',
          'User-Agent': USER_AGENT,
          Accept: '*/*'
        }
      },
      (response) => {
        this.response = response;
        const interval = Number.parseInt(response.headers['icy-metaint'], 10);
        const stationName = response.headers['icy-name'];

        this.emit('headers', {
          statusCode: response.statusCode,
          stationName,
          contentType: response.headers['content-type'],
          metadataInterval: Number.isFinite(interval) ? interval : null
        });

        if (!Number.isFinite(interval) || interval <= 0) {
          this.emit('unavailable', 'Stream did not provide icy-metaint.');
          response.resume();
          return;
        }

        this.consume(response, interval);
      }
    );

    this.request.on('error', (error) => {
      if (this.active) this.emit('error', error);
    });

    this.request.setTimeout(15000, () => {
      this.request.destroy(new Error('ICY metadata request timed out.'));
    });
  }

  stop() {
    this.active = false;
    if (this.response && this.response.destroy) this.response.destroy();
    if (this.request && this.request.destroy) this.request.destroy();
    this.response = null;
    this.request = null;
  }

  consume(response, interval) {
    let buffer = Buffer.alloc(0);
    let bytesUntilMetadata = interval;
    let metadataLength = null;

    response.on('data', (chunk) => {
      if (!this.active) return;
      buffer = Buffer.concat([buffer, chunk]);

      while (buffer.length > 0) {
        if (metadataLength === null) {
          if (bytesUntilMetadata > buffer.length) {
            bytesUntilMetadata -= buffer.length;
            buffer = Buffer.alloc(0);
            return;
          }

          buffer = buffer.subarray(bytesUntilMetadata);
          bytesUntilMetadata = interval;

          if (buffer.length < 1) return;
          metadataLength = buffer[0] * 16;
          buffer = buffer.subarray(1);
        }

        if (metadataLength > buffer.length) return;

        const metadataBuffer = buffer.subarray(0, metadataLength);
        buffer = buffer.subarray(metadataLength);
        metadataLength = null;

        const metadata = metadataBuffer.toString('utf8').replace(/\0+$/g, '');
        this.handleMetadata(metadata);
      }
    });

    response.on('end', () => {
      if (this.active) this.emit('end');
    });

    response.on('error', (error) => {
      if (this.active) this.emit('error', error);
    });
  }

  handleMetadata(metadata) {
    if (!metadata) return;

    const parsed = parseIcyMetadata(metadata);
    const trackTitle = normalizeTrackTitle(parsed.StreamTitle);

    this.emit('metadata', {
      raw: metadata,
      parsed,
      trackTitle
    });

    if (trackTitle && trackTitle !== this.lastTrackTitle) {
      const previousTrackTitle = this.lastTrackTitle;
      this.lastTrackTitle = trackTitle;
      this.emit('trackChange', {
        previousTrackTitle,
        trackTitle
      });
    }
  }
}

module.exports = { IcyMetadataReader };
