/**
 * 666RadioCoreDJ | src/radio/adapters/shoutcastAdapter.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Optionaler SHOUTcast-Fallback. Kickt die Source, ist kein sauberer AutoDJ-Skip.
 */
const { request, basicAuthHeader } = require('../../utils/httpClient');

class ShoutcastAdapter {
  constructor(config) {
    this.config = config;
  }

  buildKickSourceUrl() {
    if (!this.config.adminCgiUrl) return '';
    const url = new URL(this.config.adminCgiUrl);
    url.searchParams.set('sid', this.config.sid || '1');
    url.searchParams.set('mode', 'kicksrc');

    // Nur aktivieren, wenn der Server zwingend pass= verlangt. Basic Auth ist sauberer.
    if (this.config.passQueryEnabled && this.config.adminPass) {
      url.searchParams.set('pass', this.config.adminPass);
    }

    return url.toString();
  }

  async kickSource() {
    const url = this.buildKickSourceUrl();
    if (!url) {
      return {
        ok: false,
        adapter: 'shoutcast',
        code: 'SHOUTCAST_ADMIN_URL_MISSING',
        message: 'SHOUTcast Admin-CGI-URL fehlt.'
      };
    }

    const headers = {
      'User-Agent': '666RadioCoreDJ/1.0.0',
      'Accept': 'text/html,text/plain,*/*'
    };

    if (!this.config.passQueryEnabled && this.config.adminPass) {
      headers.Authorization = basicAuthHeader(this.config.adminUser || 'admin', this.config.adminPass);
    }

    const response = await request({ url, method: 'GET', headers });

    return {
      ok: response.ok,
      adapter: 'shoutcast',
      code: response.ok ? 'SHOUTCAST_KICKSRC_SENT' : 'SHOUTCAST_KICKSRC_HTTP_ERROR',
      status: response.status,
      message: response.ok
        ? 'SHOUTcast kicksrc wurde ausgelöst. Achtung: Das ist nur ein Fallback, kein echter SonicPanel-AutoDJ-Skip.'
        : `SHOUTcast antwortete mit HTTP ${response.status}.`,
      detail: response.body
    };
  }
}

module.exports = { ShoutcastAdapter };
