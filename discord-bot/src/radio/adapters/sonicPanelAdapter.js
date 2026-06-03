/**
 * 666RadioCoreDJ | src/radio/adapters/sonicPanelAdapter.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: SonicPanel/MyIDJ-Steueradapter für AutoDJ-Skip und Jingle/ID On-Air.
 * Hinweis: Der echte SonicPanel-Button-Request muss aus dem DJ-Panel-Netzwerk-Tab eingetragen werden.
 */
const { request, basicAuthHeader } = require('../../utils/httpClient');

class SonicPanelAdapter {
  constructor(config) {
    this.config = config;
  }

  buildHeaders(authMode, bearerToken) {
    const headers = {
      'User-Agent': '666RadioCoreDJ/1.0.0',
      'Accept': 'application/json,text/plain,text/html,*/*'
    };

    if (authMode === 'basic') {
      headers.Authorization = basicAuthHeader(this.config.djUser, this.config.djPass);
    }

    if (authMode === 'bearer' && bearerToken) {
      headers.Authorization = `Bearer ${bearerToken}`;
    }

    return headers;
  }

  async skipTrack() {
    if (!this.config.skipUrl) {
      return {
        ok: false,
        adapter: 'sonicpanel',
        code: 'SONICPANEL_SKIP_URL_MISSING',
        message: 'SonicPanel Skip-URL fehlt. Bitte echten Skip-Request aus dem DJ-Panel-Netzwerk-Tab eintragen.'
      };
    }

    const response = await request({
      url: this.config.skipUrl,
      method: this.config.skipMethod,
      headers: this.buildHeaders(this.config.skipAuth, this.config.skipBearerToken)
    });

    return {
      ok: response.ok,
      adapter: 'sonicpanel',
      code: response.ok ? 'SONICPANEL_SKIP_SENT' : 'SONICPANEL_SKIP_HTTP_ERROR',
      status: response.status,
      message: response.ok ? 'SonicPanel AutoDJ-Skip wurde ausgelöst.' : `SonicPanel antwortete mit HTTP ${response.status}.`,
      detail: response.body
    };
  }

  async playJingle(nameOrId) {
    if (!this.config.jingleUrlTemplate) {
      return {
        ok: false,
        adapter: 'sonicpanel',
        code: 'SONICPANEL_JINGLE_URL_MISSING',
        message: 'SonicPanel Jingle-URL-Template fehlt. Bitte echten Jingle/ID-Request aus dem DJ-Panel-Netzwerk-Tab eintragen.'
      };
    }

    const safeValue = encodeURIComponent(nameOrId || '');
    const url = this.config.jingleUrlTemplate
      .replaceAll('{name}', safeValue)
      .replaceAll('{id}', safeValue);

    const response = await request({
      url,
      method: this.config.jingleMethod,
      headers: this.buildHeaders(this.config.jingleAuth, this.config.jingleBearerToken)
    });

    return {
      ok: response.ok,
      adapter: 'sonicpanel',
      code: response.ok ? 'SONICPANEL_JINGLE_SENT' : 'SONICPANEL_JINGLE_HTTP_ERROR',
      status: response.status,
      message: response.ok ? `SonicPanel Jingle/ID wurde ausgelöst: ${nameOrId}` : `SonicPanel antwortete mit HTTP ${response.status}.`,
      detail: response.body
    };
  }
}

module.exports = { SonicPanelAdapter };
