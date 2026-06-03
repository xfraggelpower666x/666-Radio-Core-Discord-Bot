/**
 * 666RadioCoreDJ | src/utils/httpClient.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Kleine Fetch-Hilfe mit Timeout, Basic/Bearer-Auth und sicherem Fehlertext.
 */
const { redact } = require('./redact');

async function request({ url, method = 'GET', headers = {}, body, timeoutMs = 12000 }) {
  if (!url) {
    throw new Error('HTTP request URL fehlt.');
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      method,
      headers,
      body,
      signal: controller.signal
    });

    const text = await response.text().catch(() => '');

    return {
      ok: response.ok,
      status: response.status,
      statusText: response.statusText,
      body: redact(text.slice(0, 1000))
    };
  } catch (error) {
    const cleanMessage = error && error.message ? redact(error.message) : 'Unbekannter HTTP Fehler';
    throw new Error(cleanMessage);
  } finally {
    clearTimeout(timer);
  }
}

function basicAuthHeader(user, pass) {
  const token = Buffer.from(`${user || ''}:${pass || ''}`).toString('base64');
  return `Basic ${token}`;
}

module.exports = { request, basicAuthHeader };
