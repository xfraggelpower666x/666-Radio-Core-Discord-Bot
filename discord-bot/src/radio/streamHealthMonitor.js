/**
 * 666RadioCoreDJ | src/radio/streamHealthMonitor.js
 * Zweck: SHOUTcast/Icecast-Stream per HTTP prüfen und Statuswechsel melden.
 */
const { EventEmitter } = require('events');

class StreamHealthMonitor extends EventEmitter {
  constructor({ intervalMs, timeoutMs, logger: monitorLogger = null }) {
    super();
    this.intervalMs = intervalMs;
    this.timeoutMs = timeoutMs;
    this.logger = monitorLogger;
    this.timer = null;
    this.streamUrl = null;
    this.lastStatus = {
      healthy: false,
      checkedAt: null,
      statusCode: null,
      contentType: null,
      error: 'not-started'
    };
  }

  start(streamUrl) {
    this.stop();
    this.streamUrl = streamUrl;
    this.check();
    this.timer = setInterval(() => this.check(), this.intervalMs);
    if (this.timer.unref) this.timer.unref();
  }

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.streamUrl = null;
  }

  snapshot() {
    return { ...this.lastStatus };
  }

  async check() {
    if (!this.streamUrl) return;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(this.streamUrl, {
        method: 'GET',
        headers: {
          Range: 'bytes=0-0',
          'User-Agent': '666-Radio-Core-Discord-Bot/1.3'
        },
        signal: controller.signal
      });

      const healthy = response.ok || response.status === 206;
      this.updateStatus({
        healthy,
        checkedAt: new Date().toISOString(),
        statusCode: response.status,
        contentType: response.headers.get('content-type'),
        error: healthy ? null : `unexpected-status-${response.status}`
      });
    } catch (error) {
      this.updateStatus({
        healthy: false,
        checkedAt: new Date().toISOString(),
        statusCode: null,
        contentType: null,
        error: error.name === 'AbortError' ? 'timeout' : error.message
      });
    } finally {
      clearTimeout(timeout);
    }
  }

  updateStatus(nextStatus) {
    const wasHealthy = this.lastStatus.healthy;
    this.lastStatus = nextStatus;
    this.emit('status', nextStatus);

    if (wasHealthy !== nextStatus.healthy) {
      this.emit(nextStatus.healthy ? 'healthy' : 'unhealthy', nextStatus);
    }
  }
}

module.exports = { StreamHealthMonitor };
