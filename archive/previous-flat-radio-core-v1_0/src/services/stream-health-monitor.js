import { EventEmitter } from 'node:events';

export class StreamHealthMonitor extends EventEmitter {
  constructor({ intervalMs, timeoutMs, logger = null }) {
    super();
    this.intervalMs = intervalMs;
    this.timeoutMs = timeoutMs;
    this.logger = logger;
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
    this.timer.unref?.();
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
          'User-Agent': '666-Radio-Core-Discord-Bot/1.0'
        },
        signal: controller.signal
      });

      const healthy = response.ok || response.status === 206;
      const nextStatus = {
        healthy,
        checkedAt: new Date().toISOString(),
        statusCode: response.status,
        contentType: response.headers.get('content-type'),
        error: healthy ? null : `unexpected-status-${response.status}`
      };

      this.updateStatus(nextStatus);
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
