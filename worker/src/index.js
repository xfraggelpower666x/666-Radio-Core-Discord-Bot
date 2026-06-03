/**
 * 666RadioCoreDJ Worker | src/index.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Version: v1.3.0
 * Zweck: Cloudflare Worker API-Layer für Health, NowPlaying und Stream-Presets.
 * Hinweis: Dieser Worker ist nicht der Discord-Voice-Bot. Keine Secrets im Code ausgeben.
 */

const JSON_HEADERS = {
  'content-type': 'application/json; charset=utf-8',
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'GET, OPTIONS',
  'access-control-allow-headers': 'content-type, authorization'
};

function json(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: JSON_HEADERS
  });
}

function bool(value, fallback = false) {
  if (value === undefined || value === null || value === '') return fallback;
  return ['1', 'true', 'yes', 'ja', 'on'].includes(String(value).toLowerCase());
}

function getPreset(env, id) {
  const safeId = String(id || '').replace(/[^1-5]/g, '');
  if (!safeId || !['1', '2', '3', '4', '5'].includes(safeId)) return null;

  const name = env[`PRESET_${safeId}_NAME`] || `Stream ${safeId}`;
  const url = env[`PRESET_${safeId}_URL`] || '';
  const exposeUrl = bool(env.PUBLIC_PRESET_URLS, false);

  return {
    id: safeId,
    name,
    configured: Boolean(url),
    url: exposeUrl ? url : undefined
  };
}

function getAllPresets(env) {
  return ['1', '2', '3', '4', '5'].map((id) => getPreset(env, id));
}

async function fetchNowPlaying(env) {
  const statusUrl = env.SHOUTCAST_PUBLIC_STATUS_URL || '';
  if (!statusUrl) {
    return {
      configured: false,
      source: 'none',
      message: 'SHOUTCAST_PUBLIC_STATUS_URL ist nicht gesetzt.'
    };
  }

  try {
    const response = await fetch(statusUrl, {
      headers: { accept: 'application/json,text/plain,*/*' }
    });

    const contentType = response.headers.get('content-type') || '';
    const text = await response.text();
    let parsed = null;

    if (contentType.includes('json') || text.trim().startsWith('{') || text.trim().startsWith('[')) {
      try {
        parsed = JSON.parse(text);
      } catch (_error) {
        parsed = null;
      }
    }

    const title = extractTitle(parsed, text);

    return {
      configured: true,
      ok: response.ok,
      status: response.status,
      source: 'public-status-url',
      title: title || null,
      rawType: parsed ? 'json' : 'text'
    };
  } catch (error) {
    return {
      configured: true,
      ok: false,
      source: 'public-status-url',
      message: error.message
    };
  }
}

function extractTitle(parsed, text) {
  if (parsed && typeof parsed === 'object') {
    const candidates = [
      parsed.songtitle,
      parsed.servertitle,
      parsed.title,
      parsed.nowplaying,
      parsed.current_song,
      parsed.currentSong,
      parsed?.icestats?.source?.title,
      parsed?.icestats?.source?.yp_currently_playing
    ];

    for (const candidate of candidates) {
      if (typeof candidate === 'string' && candidate.trim()) return candidate.trim();
    }
  }

  if (typeof text === 'string') {
    const match = text.match(/<SONGTITLE>(.*?)<\/SONGTITLE>/i) || text.match(/<TITLE>(.*?)<\/TITLE>/i);
    if (match && match[1]) return match[1].trim();
  }

  return '';
}

function routeInfo(env, request) {
  const url = new URL(request.url);
  return {
    service: '666RadioCoreDJ Worker',
    version: env.WORKER_VERSION || '1.3.0',
    routes: [
      'GET /health',
      'GET /nowplaying',
      'GET /presets',
      'GET /preset/1',
      'GET /preset/2',
      'GET /preset/3',
      'GET /preset/4',
      'GET /preset/5'
    ],
    path: url.pathname
  };
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: JSON_HEADERS });
    }

    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';

    if (request.method !== 'GET') {
      return json({ ok: false, error: 'METHOD_NOT_ALLOWED' }, 405);
    }

    if (path === '/' || path === '/help') {
      return json(routeInfo(env, request));
    }

    if (path === '/health') {
      return json({
        ok: true,
        service: '666RadioCoreDJ Worker',
        version: env.WORKER_VERSION || '1.3.0',
        defaultPreset: env.DEFAULT_PRESET || '1',
        presetsConfigured: getAllPresets(env).filter((preset) => preset.configured).length,
        timestamp: new Date().toISOString()
      });
    }

    if (path === '/presets') {
      return json({
        ok: true,
        defaultPreset: env.DEFAULT_PRESET || '1',
        publicPresetUrls: bool(env.PUBLIC_PRESET_URLS, false),
        presets: getAllPresets(env)
      });
    }

    const presetMatch = path.match(/^\/preset\/([1-5])$/);
    if (presetMatch) {
      const preset = getPreset(env, presetMatch[1]);
      return json({ ok: Boolean(preset), preset }, preset ? 200 : 404);
    }

    if (path === '/nowplaying') {
      const nowplaying = await fetchNowPlaying(env);
      return json({ ok: Boolean(nowplaying.ok || !nowplaying.configured), nowplaying });
    }

    return json({ ok: false, error: 'NOT_FOUND', ...routeInfo(env, request) }, 404);
  }
};
