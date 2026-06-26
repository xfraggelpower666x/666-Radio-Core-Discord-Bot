// ============================================================
// 666 RadioBotAI — Vocard Sovereign Dashboard Worker
// Version: v1.2.2
//
// Zweck:
// - Cloudflare Worker API fuer RadioBotAI
// - Vocard-basierter Dashboard-Einstieg
// - Stream-/NowPlaying-/Status-Bridge
// - Discord-Shooter Control Panel ohne Webhook-Secrets im Frontend
//
// Wichtig:
// - Dieser Worker ist NICHT der Discord Voice Bot.
// - Der Voice Bot bleibt ein separater Discord-Bot-Prozess.
// - Echte Secrets bleiben in Cloudflare Secrets / Host ENV.
// ============================================================

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-allow-headers": "content-type"
};

function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { ...JSON_HEADERS, ...extraHeaders }
  });
}

function html(data, status = 200) {
  return new Response(data, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "access-control-allow-origin": "*"
    }
  });
}

function text(data, status = 200) {
  return new Response(data, {
    status,
    headers: {
      "content-type": "text/plain; charset=utf-8",
      "access-control-allow-origin": "*"
    }
  });
}

function getPublicConfig(env) {
  const base = env.PUBLIC_WEBRADIO_BASE_URL || "https://webradio.666soundsdesign-broadcaster.com";
  return {
    projectName: env.PUBLIC_PROJECT_NAME || "666SOUNDsDESIGn WebRadio",
    botName: env.PUBLIC_BOT_NAME || "666 RadioBotAI",
    version: env.PUBLIC_VERSION || "v1.2.2-audit-split-real-skip",
    role: env.PUBLIC_WORKER_ROLE || "RadioBotAI API / Vocard Dashboard Bridge / Discord Shooter Control",
    webradioBaseUrl: base,
    streamUrl: env.PUBLIC_MAIN_STREAM_URL || `${base}/stream`,
    fallbackStreamUrl: env.PUBLIC_FALLBACK_STREAM_URL || `${base}/fallback-stream`,
    nowPlayingUrl: env.PUBLIC_NOWPLAYING_URL || `${base}/api/nowplaying`,
    healthUrl: env.PUBLIC_HEALTH_URL || `${base}/health`,
    tuneInUrl: env.PUBLIC_TUNEIN_URL || "https://tunein.com/radio/s357001",
    playerAlertBackendUrl: env.PLAYER_ALERT_BACKEND_URL || env.RENDA_PLAYER_ALERT_URL || env.RENDER_PLAYER_ALERT_URL || env.RENDA_BACKEND_URL || env.RENDER_BACKEND_URL || "",
    dashboardUrl: "/dashboard",
    workerEndpoints: [
      "/health",
      "/status",
      "/nowplaying",
      "/stream",
      "/dashboard",
      "/config/public",
      "/api/discord/status",
      "/api/discord/debug",
      "/api/discord/manual",
      "/api/discord/message",
      "/api/discord/nowplaying",
      "/api/discord/test",
      "/api/player-alert/status",
      "/api/player-alert/send",
      "/api/player-alert/current",
      "/api/player-alert/history",
      "/render/status",
      "/auth/status",
      "/auth/verify",
      "/admin/status",
      "/admin/protected-test",
      "/radio/autodj/status",
      "/radio/autodj/skip",
      "/api/radio/skip",
      "/autodj/skip",
      "/radio/autodj/playlist",
      "/preset/1",
      "/preset/2",
      "/preset/3",
      "/preset/4",
      "/preset/5"
    ]
  };
}

async function safeFetchJson(url, init = {}) {
  if (!url) return { ok: false, error: "missing_url" };
  try {
    const response = await fetch(url, init);
    const textBody = await response.text();
    let data = null;
    try { data = textBody ? JSON.parse(textBody) : null; } catch (_) {}
    return {
      ok: response.ok,
      status: response.status,
      data: data || textBody.slice(0, 1000)
    };
  } catch (error) {
    return { ok: false, status: 0, error: String(error?.message || error) };
  }
}

function getAuthConfig(env) {
  return {
    adminTokenEnabled: Boolean(env.DISCORD_ADMIN_TOKEN || env.ADMIN_TOKEN),
    gateCodeEnabled: Boolean(env.DISCORD_GATE_CODE || env.DISCORD_GATE_SHA256),
    legacyGateHashEnabled: Boolean(env.DISCORD_GATE_SHA256),
    adminAuthVerifyUrl: env.ADMIN_AUTH_VERIFY_URL || env.AUTH_VERIFY_URL || "",
    adminAuthLoginUrl: env.ADMIN_AUTH_LOGIN_URL || env.AUTH_LOGIN_URL || "",
    passwordWorkerUrl: env.ADMIN_PASSWORD_VERIFY_URL || env.ADMIN_PW_VERIFY_URL || env.PASSWORD_VERIFY_URL || env.PW_VERIFY_URL || "",
    authAudience: env.AUTH_AUDIENCE || "666RadioBotAI",
    authMode: env.AUTH_MODE || "hybrid"
  };
}

function publicAuthStatus(env) {
  const cfg = getAuthConfig(env);
  return {
    adminTokenEnabled: cfg.adminTokenEnabled,
    gateCodeEnabled: cfg.gateCodeEnabled,
    legacyGateHashEnabled: cfg.legacyGateHashEnabled,
    adminAuthWorkerConfigured: Boolean(cfg.adminAuthVerifyUrl),
    passwordWorkerConfigured: Boolean(cfg.passwordWorkerUrl),
    authAudience: cfg.authAudience,
    authMode: cfg.authMode,
    note: "No token, password, cookie or secret value is exposed."
  };
}

async function verifyExternalAuthWorker(request, env, authHeader) {
  const cfg = getAuthConfig(env);
  if (!cfg.adminAuthVerifyUrl || !authHeader) return { ok: false, method: "admin-auth-worker", reason: "missing_verify_url_or_authorization" };

  // First try POST JSON because many auth bridges accept a compact verification payload.
  const postResult = await safeFetchJson(cfg.adminAuthVerifyUrl, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "authorization": authHeader,
      "x-auth-audience": cfg.authAudience
    },
    body: JSON.stringify({ audience: cfg.authAudience, source: "666radiobotai-worker" })
  });

  if (postResult.ok && (postResult.data?.ok || postResult.data?.authorized || postResult.data?.valid || postResult.data?.authenticated)) {
    return { ok: true, method: "admin-auth-worker-post" };
  }

  // Fallback GET for older worker contracts.
  const getResult = await safeFetchJson(cfg.adminAuthVerifyUrl, {
    method: "GET",
    headers: {
      "authorization": authHeader,
      "x-auth-audience": cfg.authAudience
    }
  });

  if (getResult.ok && (getResult.data?.ok || getResult.data?.authorized || getResult.data?.valid || getResult.data?.authenticated)) {
    return { ok: true, method: "admin-auth-worker-get" };
  }

  return { ok: false, method: "admin-auth-worker", reason: "external_auth_rejected", status: postResult.status || getResult.status || 0 };
}

async function verifyPasswordWorker(request, env, body = null) {
  const cfg = getAuthConfig(env);
  if (!cfg.passwordWorkerUrl) return { ok: false, method: "password-worker", reason: "not_configured" };

  const payload = body || await requestBody(request);
  const password = payload.password || payload.pass || payload.gate || payload.code || "";
  if (!password) return { ok: false, method: "password-worker", reason: "missing_password_payload" };

  const result = await safeFetchJson(cfg.passwordWorkerUrl, {
    method: "POST",
    headers: { "content-type": "application/json", "x-auth-audience": cfg.authAudience },
    body: JSON.stringify({ password, audience: cfg.authAudience, source: "666radiobotai-dashboard" })
  });

  if (result.ok && (result.data?.ok || result.data?.authorized || result.data?.valid || result.data?.authenticated)) {
    return { ok: true, method: "password-worker" };
  }

  return { ok: false, method: "password-worker", reason: "password_worker_rejected", status: result.status || 0 };
}

async function verifyAdmin(request, env, body = null) {
  const adminToken = env.DISCORD_ADMIN_TOKEN || env.ADMIN_TOKEN || "";
  const gateCode = env.DISCORD_GATE_CODE || "";
  const providedToken = request.headers.get("x-admin-token") || "";
  const providedGate = request.headers.get("x-discord-gate-code") || "";
  const auth = request.headers.get("authorization") || "";

  if (adminToken && providedToken && providedToken === adminToken) {
    return { ok: true, method: "x-admin-token" };
  }

  if (gateCode && providedGate && providedGate === gateCode) {
    return { ok: true, method: "x-discord-gate-code" };
  }

  const external = await verifyExternalAuthWorker(request, env, auth);
  if (external.ok) return external;

  // Passwort-Worker nur bei POST/Payload verwenden, damit GET-Status nie versehentlich sensible Werte verlangt.
  if (request.method === "POST") {
    const pw = await verifyPasswordWorker(request, env, body);
    if (pw.ok) return pw;
  }

  return { ok: false, method: "none" };
}

function forwardHeaders(request, env) {
  const headers = { "content-type": "application/json" };
  const adminToken = request.headers.get("x-admin-token");
  const gateCode = request.headers.get("x-discord-gate-code");
  const auth = request.headers.get("authorization");
  if (adminToken) headers["x-admin-token"] = adminToken;
  if (gateCode) headers["x-discord-gate-code"] = gateCode;
  if (auth) headers["authorization"] = auth;
  return headers;
}

async function handleRoot(env) {
  const cfg = getPublicConfig(env);
  return json({
    ok: true,
    service: cfg.botName,
    project: cfg.projectName,
    role: cfg.role,
    version: cfg.version,
    dashboard: cfg.dashboardUrl,
    note: "Cloudflare Worker API layer. Discord Voice Bot runs separately.",
    endpoints: cfg.workerEndpoints
  });
}

async function handleHealth(env) {
  const cfg = getPublicConfig(env);
  const radio = await safeFetchJson(cfg.healthUrl);
  return json({
    ok: true,
    service: cfg.botName,
    project: cfg.projectName,
    version: cfg.version,
    worker: "666radiobotai",
    radioHealth: {
      checked: !!cfg.healthUrl,
      ok: radio.ok,
      status: radio.status || 0
    },
    timestamp: new Date().toISOString()
  });
}

async function handleStatus(env) {
  const cfg = getPublicConfig(env);
  const radioHealth = await safeFetchJson(cfg.healthUrl);
  const nowPlaying = await safeFetchJson(cfg.nowPlayingUrl);
  return json({
    ok: true,
    bot: {
      name: cfg.botName,
      type: "Discord Voice Radio Bot / WebRadio Stream Player",
      state: "worker_online",
      note: "Voice runtime status must be reported by the separate Discord bot process when connected."
    },
    worker: {
      name: "666radiobotai",
      version: cfg.version,
      role: cfg.role
    },
    radio: {
      baseUrl: cfg.webradioBaseUrl,
      streamUrl: cfg.streamUrl,
      fallbackStreamUrl: cfg.fallbackStreamUrl,
      healthOk: radioHealth.ok,
      healthStatus: radioHealth.status || 0,
      nowPlayingOk: nowPlaying.ok,
      nowPlayingStatus: nowPlaying.status || 0
    },
    dashboard: {
      basis: "Vocard Dashboard source preserved under Dashboard/Vocard-Dashboard-main",
      extension: "RadioBotAI Cyberstream Dashboard Addon"
    },
    timestamp: new Date().toISOString()
  });
}

async function handleNowPlaying(env) {
  const cfg = getPublicConfig(env);
  const upstream = await safeFetchJson(cfg.nowPlayingUrl);
  if (upstream.ok) {
    return json({
      ok: true,
      source: cfg.nowPlayingUrl,
      upstream: upstream.data,
      timestamp: new Date().toISOString()
    });
  }
  return json({
    ok: false,
    error: "NOWPLAYING_UPSTREAM_UNAVAILABLE",
    source: cfg.nowPlayingUrl,
    upstream,
    fallback: {
      artist: null,
      title: null,
      raw: null
    },
    timestamp: new Date().toISOString()
  }, 502);
}

async function handleStream(env) {
  const cfg = getPublicConfig(env);
  return json({
    ok: true,
    streams: {
      main: cfg.streamUrl,
      fallback: cfg.fallbackStreamUrl,
      tuneIn: cfg.tuneInUrl,
      website: cfg.webradioBaseUrl
    }
  });
}

async function handlePreset(request, env, presetId) {
  const allowed = ["1", "2", "3", "4", "5"];
  if (!allowed.includes(presetId)) {
    return json({ ok: false, error: "INVALID_PRESET", preset: presetId }, 400);
  }

  if (request.method === "POST") {
    const body = await requestBody(request);
    const auth = await verifyAdmin(request, env, body);
    if (!auth.ok) {
      return json({
        ok: false,
        error: "UNAUTHORIZED",
        preset: presetId,
        note: "Preset switching is protected. Provide admin token, gate code or valid auth worker token.",
        auth: publicAuthStatus(env)
      }, 401);
    }
    return json({
      ok: true,
      protected: true,
      auth: auth.method,
      action: "PRESET_REQUEST_AUTHORIZED",
      preset: presetId,
      note: "Preset endpoint authorized. Real SonicPanel/AutoDJ switching remains a next integration step.",
      timestamp: new Date().toISOString()
    });
  }

  return json({
    ok: true,
    protected: false,
    action: "PRESET_STATUS_ONLY",
    preset: presetId,
    note: "GET is read-only. POST requires admin/auth protection.",
    timestamp: new Date().toISOString()
  });
}

async function handleAuthStatus(env) {
  return json({
    ok: true,
    auth: publicAuthStatus(env),
    protectedRoutes: [
      "POST /api/discord/message",
      "POST /api/discord/manual",
      "POST /api/discord/nowplaying",
      "POST /api/discord/test",
      "POST /preset/1..5",
      "GET/POST /admin/status",
      "GET/POST /admin/protected-test"
    ],
    timestamp: new Date().toISOString()
  });
}

async function handleAuthVerify(request, env) {
  const body = request.method === "POST" ? await requestBody(request) : null;
  const result = await verifyAdmin(request, env, body);
  return json({
    ok: result.ok,
    authenticated: result.ok,
    method: result.method,
    auth: publicAuthStatus(env),
    timestamp: new Date().toISOString()
  }, result.ok ? 200 : 401);
}

async function handleAdminStatus(request, env) {
  const result = await verifyAdmin(request, env);
  if (!result.ok) {
    return json({ ok: false, error: "UNAUTHORIZED", auth: publicAuthStatus(env) }, 401);
  }
  return json({
    ok: true,
    authenticated: true,
    method: result.method,
    admin: {
      dashboardControls: "enabled",
      discordShooter: "protected",
      presets: "protected_on_post",
      secretsExposed: false
    },
    discord: publicTargetStatus(env),
    auth: publicAuthStatus(env),
    timestamp: new Date().toISOString()
  });
}

async function handleAdminProtectedTest(request, env) {
  const body = request.method === "POST" ? await requestBody(request) : null;
  const result = await verifyAdmin(request, env, body);
  if (!result.ok) return json({ ok: false, error: "UNAUTHORIZED", auth: publicAuthStatus(env) }, 401);
  return json({
    ok: true,
    message: "Admin/Auth protection is active.",
    method: result.method,
    timestamp: new Date().toISOString()
  });
}


// ============================================================
// PLAYER_ALERT_RENDER_BRIDGE_V1_1_3
// Aus WebRadio-Code zerlegt und fuer RadioBotAI uebernommen.
// Fallback-Reihenfolge: Render Backend -> KV -> Cloudflare Cache.
// Zweck: Dashboard/Broadcast-Nachrichten als Backend-primary Relay.
// ============================================================
const PLAYER_ALERT_CACHE_KEY = "https://666radiobotai.local/player-alert/current";
const PLAYER_ALERT_RATE_KEY = "https://666radiobotai.local/player-alert/rate";
const PLAYER_ALERT_RATE_MS = 180000;
const PLAYER_ALERT_KV_CURRENT_KEY = "player-alert:current";
const PLAYER_ALERT_KV_RATE_KEY = "player-alert:rate";
const PLAYER_ALERT_KV_HISTORY_KEY = "player-alert:history";

function playerAlertCleanText(value, max = 240) {
  return String(value || "")
    .replace(/[<>]/g, "")
    .replace(/[\u0000-\u001f\u007f]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max);
}

function playerAlertBackendUrl(env) {
  const raw = (env && (env.PLAYER_ALERT_BACKEND_URL || env.RENDA_PLAYER_ALERT_URL || env.RENDER_PLAYER_ALERT_URL || env.RENDA_BACKEND_URL || env.RENDER_BACKEND_URL)) || "";
  if (!raw) return "";
  try {
    const url = new URL(String(raw));
    if (!/\/api\/player-alert\/?$/.test(url.pathname)) {
      url.pathname = url.pathname.replace(/\/$/, "") + "/api/player-alert";
    }
    return url.toString();
  } catch (_) {
    return "";
  }
}

async function playerAlertBackendFetch(env, path, init = {}) {
  const base = playerAlertBackendUrl(env);
  if (!base) return null;
  const url = new URL(base);
  url.pathname = url.pathname.replace(/\/$/, "") + path;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 6500);
  const backendToken = String(env.PLAYER_ALERT_BACKEND_TOKEN || env.PLAYER_ALERT_TOKEN || "").trim();
  const headers = { "content-type": "application/json", ...(init.headers || {}) };
  if (backendToken) headers["x-player-alert-token"] = backendToken;
  try {
    const response = await fetch(url.toString(), {
      signal: controller.signal,
      headers,
      ...init
    });
    clearTimeout(timer);
    const textBody = await response.text().catch(() => "");
    let data = null;
    try { data = textBody ? JSON.parse(textBody) : null; } catch (_) {}
    return { ok: response.ok, status: response.status, data: data || { text: textBody.slice(0, 1000) } };
  } catch (error) {
    clearTimeout(timer);
    return { ok: false, status: 0, data: { ok: false, error: "backend_unreachable", detail: String(error?.message || error) } };
  }
}

async function playerAlertKvGet(env, key) {
  try { if (env && env.PLAYER_ALERT_KV) return await env.PLAYER_ALERT_KV.get(key, { type: "json" }); } catch (_) {}
  return null;
}

async function playerAlertKvPut(env, key, value, ttl = 900) {
  try {
    if (env && env.PLAYER_ALERT_KV) {
      await env.PLAYER_ALERT_KV.put(key, JSON.stringify(value), { expirationTtl: ttl });
      return true;
    }
  } catch (_) {}
  return false;
}

async function playerAlertHistoryAppend(env, alert) {
  const current = await playerAlertKvGet(env, PLAYER_ALERT_KV_HISTORY_KEY) || [];
  const next = Array.isArray(current) ? current.slice(0, 19) : [];
  next.unshift(alert);
  await playerAlertKvPut(env, PLAYER_ALERT_KV_HISTORY_KEY, next, 86400);
}

async function playerAlertCacheGet(key) {
  try {
    const hit = await caches.default.match(new Request(key));
    if (hit) return await hit.json();
  } catch (_) {}
  return null;
}

async function playerAlertCachePut(key, value, maxAge = 900) {
  try {
    await caches.default.put(new Request(key), new Response(JSON.stringify(value), {
      headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=" + String(maxAge) }
    }));
    return true;
  } catch (_) {
    return false;
  }
}

async function handlePlayerAlert(request, env) {
  const url = new URL(request.url);
  const pathname = url.pathname.replace(/\/+$/, "") || "/";

  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: JSON_HEADERS });

  if (pathname === "/render/status" && request.method === "GET") {
    const backend = playerAlertBackendUrl(env);
    const healthRoot = backend ? backend.replace(/\/api\/player-alert\/?$/, "/health") : "";
    const health = healthRoot ? await safeFetchJson(healthRoot) : { ok: false, error: "PLAYER_ALERT_BACKEND_URL_not_configured" };
    return json({
      ok: true,
      renderBackendConfigured: Boolean(backend),
      backendBase: backend ? "[configured]" : "",
      backendHealthOk: Boolean(health.ok),
      backendHealthStatus: health.status || 0,
      kvConfigured: Boolean(env && env.PLAYER_ALERT_KV),
      mode: "backend-primary-kv-fallback-cache-tertiary",
      routes: ["/api/player-alert/status", "/api/player-alert/send", "/api/player-alert/current", "/api/player-alert/history"],
      note: "Backend URL value is not exposed. Configure PLAYER_ALERT_BACKEND_URL as Worker variable."
    });
  }

  if (!pathname.startsWith("/api/player-alert")) return null;

  if (pathname === "/api/player-alert/status" && request.method === "GET") {
    const backend = await playerAlertBackendFetch(env, "/status", { method: "GET" });
    return json({
      ok: true,
      backendConfigured: Boolean(playerAlertBackendUrl(env)),
      backendOk: Boolean(backend && backend.ok),
      backendStatus: backend ? backend.status : 0,
      kvConfigured: Boolean(env && env.PLAYER_ALERT_KV),
      mode: "backend-primary-kv-fallback-cache-tertiary",
      source: backend && backend.ok ? "backend" : "worker-fallback-ready"
    });
  }

  if (pathname === "/api/player-alert/current" && request.method === "GET") {
    const backend = await playerAlertBackendFetch(env, "/current", { method: "GET" });
    if (backend && backend.ok) return json({ source: "backend", ...backend.data });
    const kv = await playerAlertKvGet(env, PLAYER_ALERT_KV_CURRENT_KEY);
    if (kv) return json({ source: "kv-fallback", ...kv });
    const cache = await playerAlertCacheGet(PLAYER_ALERT_CACHE_KEY);
    if (cache) return json({ source: "cache-tertiary", ...cache });
    return json({ ok: true, active: false, source: "none" });
  }

  if (pathname === "/api/player-alert/history" && request.method === "GET") {
    const backend = await playerAlertBackendFetch(env, "/history", { method: "GET" });
    if (backend && backend.ok) return json({ source: "backend", ...backend.data });
    const kv = await playerAlertKvGet(env, PLAYER_ALERT_KV_HISTORY_KEY) || [];
    return json({ ok: true, source: kv.length ? "kv-fallback" : "none", items: kv });
  }

  if (pathname === "/api/player-alert/send" && request.method === "POST") {
    const body = await requestBody(request);
    const auth = await verifyAdmin(request, env, body);
    if (!auth.ok) return json({ ok: false, error: "UNAUTHORIZED", auth: publicAuthStatus(env) }, 401);

    const message = playerAlertCleanText(body.message || body.text || body.content, 240);
    const senderId = playerAlertCleanText(body.senderId || body.clientId || body.sender || "radiobotai-dashboard", 80) || "radiobotai-dashboard";
    const username = playerAlertCleanText(body.username || body.name || "666 RadioBotAI", 28) || "666 RadioBotAI";
    if (!message) return json({ ok: false, error: "empty_message" }, 400);

    const now = Date.now();
    const rate = (await playerAlertKvGet(env, PLAYER_ALERT_KV_RATE_KEY)) || (await playerAlertCacheGet(PLAYER_ALERT_RATE_KEY));
    if (rate) {
      const last = Number(rate.last || 0);
      if (last && (now - last) < PLAYER_ALERT_RATE_MS) return json({ ok: false, error: "rate_limited", retryAfterMs: PLAYER_ALERT_RATE_MS - (now - last) }, 429);
    }

    const alert = {
      ok: true,
      active: true,
      id: String(now) + "-" + Math.random().toString(36).slice(2, 8),
      message,
      username,
      senderId,
      clientId: senderId,
      createdAt: new Date(now).toISOString(),
      timestamp: now,
      version: playerAlertCleanText(body.version || "v1.2.2-audit-split-real-skip", 40),
      source: "666radiobotai-worker"
    };

    const backend = await playerAlertBackendFetch(env, "/send", { method: "POST", body: JSON.stringify(alert) });
    if (backend && backend.ok) {
      await playerAlertKvPut(env, PLAYER_ALERT_KV_RATE_KEY, { last: now }, 180);
      return json({ ok: true, delivered: true, source: "backend", fallback: false, backendStatus: backend.status, data: backend.data });
    }

    const kvOk = await playerAlertKvPut(env, PLAYER_ALERT_KV_CURRENT_KEY, alert, 900);
    if (kvOk) {
      await playerAlertKvPut(env, PLAYER_ALERT_KV_RATE_KEY, { last: now }, 180);
      await playerAlertHistoryAppend(env, alert);
      return json({ source: "kv-fallback", backend: backend ? backend.data : null, ...alert });
    }

    await playerAlertCachePut(PLAYER_ALERT_CACHE_KEY, alert, 900);
    await playerAlertCachePut(PLAYER_ALERT_RATE_KEY, { last: now }, 180);
    return json({ source: "cache-tertiary", backend: backend ? backend.data : null, ...alert });
  }

  return json({ ok: false, error: "not_found", path: pathname }, 404);
}
// END PLAYER_ALERT_RENDER_BRIDGE_V1_1_3


const FALLBACK_DISCORD_GATE_SHA256 = "";
const DISCORD_RUNTIME = globalThis.__S666_RADIOBOTAI_DISCORD_RUNTIME__ || {
  lastOkAt: 0,
  lastErrorAt: 0,
  lastError: "",
  lastKind: "idle",
  lastTarget: "",
  lastTrackKey: "",
  lastTrackAt: 0
};
globalThis.__S666_RADIOBOTAI_DISCORD_RUNTIME__ = DISCORD_RUNTIME;

async function sha256Hex(value) {
  const data = new TextEncoder().encode(String(value || ""));
  const digest = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

function cleanText(value, fallback = "", max = 1200) {
  return String(value ?? fallback)
    .replace(/[\u0000-\u001F\u007F]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, max);
}

function normalizeDj(value) {
  const fallback = "666 DJ";
  const raw = cleanText(value, "", 160);
  if (!raw) return fallback;
  const lowered = raw.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  if (!lowered) return fallback;
  if (["unknown", "none", "n a", "na", "no dj", "nodj", "no dj status"].includes(lowered)) return fallback;
  if (lowered.includes("auto dj") || lowered.includes("autodj") || lowered.includes("auto-dj")) return fallback;
  return raw;
}

function discordTargets(env) {
  return {
    main: {
      key: "main",
      label: "Main / Hauptkanal",
      envName: "DISCORD_WEBHOOK_URL",
      webhook: env.DISCORD_WEBHOOK_URL || env.DISCORD_WEBHOOK || env.DISCORD_WEBHOOK_URI || env.DISCORD_WEBHOOK_ENDPOINT || env.WEBHOOK_URL || "",
      channelId: null,
      use: "manual, message, nowplaying"
    },
    url2: {
      key: "url2",
      label: "URL2 / Secondary",
      envName: "DISCORD_WEBHOOK_URL2",
      webhook: env.DISCORD_WEBHOOK_URL2 || "",
      channelId: null,
      use: "dual webhook / secondary channel from WebRadio docs"
    },
    url3: {
      key: "url3",
      label: "URL3 / Channel 1510363693622497400",
      envName: "DISCORD_WEBHOOK_URL3",
      webhook: env.DISCORD_WEBHOOK_URL3 || "",
      channelId: "1510363693622497400",
      use: "explicit mapped Discord channel"
    },
    privateTrack: {
      key: "privateTrack",
      label: "Private Track / NowPlaying Mirror",
      envName: "PRIVATE_TRACK_SHOOTER",
      webhook: env.PRIVATE_TRACK_SHOOTER || env.DISCORD_PRIVATE_TRACK_WEBHOOK_URL || env.DISCORD_PRIVATE_WEBHOOK_URL || env.DISCORD_RUBY_TRACK_WEBHOOK_URL || env.DISCORD_TRACK_PRIVATE_WEBHOOK || env.PRIVATE_DISCORD_WEBHOOK_URL || "",
      channelId: null,
      use: "optional nowplaying mirror compatibility"
    }
  };
}

function publicTargetStatus(env) {
  const targets = discordTargets(env);
  return Object.fromEntries(Object.entries(targets).map(([key, value]) => [key, {
    key,
    label: value.label,
    envName: value.envName,
    configured: Boolean(value.webhook),
    channelId: value.channelId,
    use: value.use
  }]));
}

function selectDiscordTargets(env, requestedTarget, kind) {
  const targets = discordTargets(env);
  const target = cleanText(requestedTarget || "", "", 80);

  if (target === "all") {
    return [targets.main, targets.url2, targets.url3, targets.privateTrack].filter((x) => x.webhook);
  }

  if (target && targets[target]) {
    return targets[target].webhook ? [targets[target]] : [];
  }

  if (kind === "nowplaying") {
    // WebRadio-Logik: Hauptkanal + optionale Private-/Mirror-Ziele.
    return [targets.main, targets.url2, targets.url3, targets.privateTrack].filter((x) => x.webhook);
  }

  // Manual/Message default: Hauptkanal.
  return targets.main.webhook ? [targets.main] : [];
}

function trackKeyFromInput(input) {
  const artist = cleanText(input.artist, "", 160).toLowerCase();
  const title = cleanText(input.title || input.track, "", 240).toLowerCase();
  const nowPlaying = cleanText(input.nowPlaying || input.now_playing || input.songtitle, "", 360).toLowerCase();
  return `${artist}|${title}|${nowPlaying}`.replace(/\|+/g, "|").trim();
}

async function requestBody(request) {
  try { return await request.json(); } catch (_) { return {}; }
}

function baseEmbedFields(input = {}, cfg = getPublicConfig({})) {
  const artist = cleanText(input.artist, "", 160);
  const title = cleanText(input.title || input.track, "", 220);
  const nowPlaying = cleanText(input.nowPlaying || input.now_playing || input.songtitle, "", 360);
  const dj = normalizeDj(input.dj || input.presenter || input.source);
  const listener = cleanText(input.listeners || input.listenerCount || "", "", 80);
  const bitrate = cleanText(input.bitrate || "", "", 80);

  const fields = [];
  if (nowPlaying || title || artist) fields.push({ name: "Now Playing", value: nowPlaying || [artist, title].filter(Boolean).join(" - ") || "Nicht eindeutig erkannt", inline: false });
  fields.push({ name: "DJ / Source", value: dj, inline: true });
  if (listener) fields.push({ name: "Listener", value: listener, inline: true });
  if (bitrate) fields.push({ name: "Bitrate", value: bitrate, inline: true });
  fields.push({ name: "Stream", value: cfg.streamUrl || "Stream nicht konfiguriert", inline: false });
  return fields;
}

function messagePayload(input = {}, cfg = getPublicConfig({})) {
  const message = cleanText(input.message || input.text || input.content, "666 RadioBotAI Message", 1800);
  return {
    username: "666 RadioBotAI",
    embeds: [{
      title: "💬 666 RadioBotAI — Dashboard Message",
      description: message,
      url: cfg.dashboardUrl || undefined,
      color: 0x16fff3,
      fields: baseEmbedFields(input, cfg),
      footer: { text: "666SOUNDsDESIGn • RadioBotAI Discord Shooter" },
      timestamp: new Date().toISOString()
    }]
  };
}

function manualPayload(input = {}, cfg = getPublicConfig({})) {
  const message = cleanText(input.message || input.text || input.content, "666 RadioBotAI Manual Broadcast", 1800);
  return {
    username: "666 RadioBotAI",
    embeds: [{
      title: "📡 666SOUNDsDESIGn WebRadio — Manual Broadcast",
      description: message,
      url: cfg.webradioBaseUrl,
      color: 0xff2bd6,
      fields: [
        { name: "Live Stream", value: cfg.streamUrl, inline: false },
        { name: "Dashboard", value: "https://666radiobotai.666soundsdesign-broadcaster.com/dashboard", inline: false },
        { name: "TuneIn", value: cfg.tuneInUrl, inline: false }
      ],
      footer: { text: "666SOUNDsDESIGn • Cyberstream Cockpit" },
      timestamp: new Date().toISOString()
    }]
  };
}

async function nowPlayingPayload(input = {}, cfg = getPublicConfig({})) {
  let merged = { ...input };
  if (!merged.nowPlaying && !merged.title && !merged.track) {
    const upstream = await safeFetchJson(cfg.nowPlayingUrl);
    if (upstream.ok && upstream.data && typeof upstream.data === "object") {
      merged = { ...upstream.data, ...merged };
    }
  }
  return {
    username: "666 RadioBotAI",
    embeds: [{
      title: "🎧 Now Playing — 666SOUNDsDESIGn WebRadio",
      description: cleanText(merged.nowPlaying || merged.songtitle || merged.track || merged.title || "NowPlaying wurde angefordert.", "", 1800),
      url: cfg.webradioBaseUrl,
      color: 0x22f7ff,
      fields: baseEmbedFields(merged, cfg),
      footer: { text: "666SOUNDsDESIGn • Now Playing Mirror" },
      timestamp: new Date().toISOString()
    }]
  };
}

async function sendWebhook(target, payload) {
  if (!target || !target.webhook) {
    return { ok: false, target: target?.key || "unknown", configured: false, error: "webhook_not_configured" };
  }
  const response = await fetch(String(target.webhook), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  });
  const textBody = await response.text().catch(() => "");
  return {
    ok: response.ok,
    target: target.key,
    label: target.label,
    envName: target.envName,
    channelId: target.channelId,
    status: response.status,
    body: response.ok ? "OK" : textBody.slice(0, 300)
  };
}

async function sendToDiscordTargets(env, targets, payload) {
  const results = [];
  for (const target of targets) {
    try {
      results.push(await sendWebhook(target, payload));
    } catch (error) {
      results.push({
        ok: false,
        target: target?.key || "unknown",
        label: target?.label || "unknown",
        envName: target?.envName || "",
        channelId: target?.channelId || null,
        error: String(error?.message || error)
      });
    }
  }
  const okCount = results.filter((x) => x.ok).length;
  const failCount = results.length - okCount;
  return { ok: okCount > 0 && failCount === 0, okCount, failCount, total: results.length, results };
}

async function handleDiscordStatus(env) {
  return json({
    ok: true,
    addon: "RadioBotAI Direct Discord Shooter",
    version: "v1.2.2-audit-split-real-skip",
    mode: "direct-worker-webhook-dispatch",
    targets: publicTargetStatus(env),
    protection: {
      adminTokenEnabled: Boolean(env.DISCORD_ADMIN_TOKEN || env.ADMIN_TOKEN),
      gateCodeEnabled: Boolean(env.DISCORD_GATE_CODE || env.DISCORD_GATE_SHA256),
      adminAuthWorkerConfigured: Boolean(env.ADMIN_AUTH_VERIFY_URL || env.AUTH_VERIFY_URL),
      passwordWorkerConfigured: Boolean(env.ADMIN_PASSWORD_VERIFY_URL || env.ADMIN_PW_VERIFY_URL || env.PASSWORD_VERIFY_URL || env.PW_VERIFY_URL)
    },
    runtime: {
      lastKind: DISCORD_RUNTIME.lastKind,
      lastTarget: DISCORD_RUNTIME.lastTarget,
      lastOkAt: DISCORD_RUNTIME.lastOkAt ? new Date(DISCORD_RUNTIME.lastOkAt).toISOString() : null,
      lastErrorAt: DISCORD_RUNTIME.lastErrorAt ? new Date(DISCORD_RUNTIME.lastErrorAt).toISOString() : null,
      lastError: DISCORD_RUNTIME.lastError || "",
      lastTrackKey: DISCORD_RUNTIME.lastTrackKey ? "[set]" : ""
    },
    note: "Webhook values are never exposed."
  });
}

async function handleDiscordDebug(env) {
  return handleDiscordStatus(env);
}

async function verifyDiscordAction(request, env) {
  const admin = await verifyAdmin(request, env);
  if (admin.ok) return admin;

  const providedGate = cleanText(request.headers.get("x-discord-gate-code") || "", "", 140);
  if (providedGate && env.DISCORD_GATE_SHA256) {
    const expectedHash = String(env.DISCORD_GATE_SHA256).trim().toLowerCase();
    if ((await sha256Hex(providedGate)) === expectedHash) return { ok: true, method: "legacy-gate-hash" };
  }

  return { ok: false, method: "none" };
}

async function directDiscordShooter(request, env, kind) {
  const auth = await verifyDiscordAction(request, env);
  if (!auth.ok) {
    DISCORD_RUNTIME.lastKind = "access-denied";
    return json({
      ok: false,
      error: "UNAUTHORIZED",
      note: "Admin token, gate code or auth worker verification required.",
      targets: publicTargetStatus(env)
    }, 401);
  }

  const cfg = getPublicConfig(env);
  const input = await requestBody(request);
  input.source = input.source || "666radiobotai-dashboard";
  input.bridge = "666radiobotai-worker";
  const requestedTarget = input.target || new URL(request.url).searchParams.get("target") || "";

  let payload;
  if (kind === "message") {
    if (!cleanText(input.message || input.text || input.content, "", 1800)) {
      return json({ ok: false, error: "message text missing" }, 400);
    }
    payload = messagePayload(input, cfg);
  } else if (kind === "manual" || kind === "test") {
    payload = manualPayload({
      ...input,
      message: input.message || input.text || input.content || (kind === "test" ? "666 RadioBotAI Testnachricht aus dem Dashboard." : "666 RadioBotAI Manual Broadcast")
    }, cfg);
  } else if (kind === "nowplaying") {
    const key = trackKeyFromInput(input);
    const now = Date.now();
    if (key && key === DISCORD_RUNTIME.lastTrackKey && now - DISCORD_RUNTIME.lastTrackAt < 20000) {
      DISCORD_RUNTIME.lastKind = "nowplaying-dedupe";
      return json({ ok: true, skipped: true, reason: "duplicate track cooldown", led: "dedupe" });
    }
    DISCORD_RUNTIME.lastTrackKey = key;
    DISCORD_RUNTIME.lastTrackAt = now;
    payload = await nowPlayingPayload(input, cfg);
  } else {
    return json({ ok: false, error: "UNKNOWN_DISCORD_KIND", kind }, 400);
  }

  const targets = selectDiscordTargets(env, requestedTarget, kind);
  if (!targets.length) {
    return json({
      ok: false,
      error: "NO_CONFIGURED_TARGETS",
      requestedTarget: requestedTarget || "(default)",
      targets: publicTargetStatus(env)
    }, 500);
  }

  const result = await sendToDiscordTargets(env, targets, payload);
  DISCORD_RUNTIME.lastKind = kind;
  DISCORD_RUNTIME.lastTarget = requestedTarget || (kind === "nowplaying" ? "auto-mirror" : "main");
  if (result.ok) {
    DISCORD_RUNTIME.lastOkAt = Date.now();
    DISCORD_RUNTIME.lastError = "";
  } else {
    DISCORD_RUNTIME.lastErrorAt = Date.now();
    DISCORD_RUNTIME.lastError = JSON.stringify(result.results.filter((x) => !x.ok)).slice(0, 800);
  }

  return json({
    ok: result.ok,
    type: kind,
    requestedTarget: requestedTarget || "(default)",
    auth: auth.method,
    sent: result.okCount,
    failed: result.failCount,
    total: result.total,
    results: result.results,
    note: "No webhook URLs are exposed."
  }, result.ok ? 200 : 502);
}

function dashboardHtml(env) {
  const cfg = getPublicConfig(env);
  return `<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>${cfg.botName} — Vocard Cyberstream Dashboard</title>
<style>
:root{--bg:#070914;--panel:#0d1224;--panel2:#121b33;--line:#22f7ff55;--cyan:#22f7ff;--pink:#ff2bd6;--text:#e9faff;--muted:#8ca6bd;--ok:#26ff9a;--warn:#ffcf33;--bad:#ff3864}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0%,#25103e 0,#070914 34%,#03050d 100%);color:var(--text);font-family:Inter,Roboto,system-ui,-apple-system,Segoe UI,sans-serif}header{padding:24px 18px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#080d1f,#160d2b,#081326);box-shadow:0 0 35px #22f7ff20}.wrap{max-width:1280px;margin:0 auto}.brand{display:flex;align-items:center;gap:14px}.logo{width:54px;height:54px;border-radius:16px;background:linear-gradient(135deg,var(--cyan),var(--pink));box-shadow:0 0 28px #ff2bd655;display:grid;place-items:center;color:#05070d;font-weight:900}.brand h1{margin:0;font-size:clamp(24px,4vw,42px);letter-spacing:.04em;text-shadow:0 0 18px #22f7ff55}.brand p{margin:4px 0 0;color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}.tab{border:1px solid var(--line);background:#0b1020;color:var(--text);padding:10px 14px;border-radius:999px;cursor:pointer}.tab.active,.tab:hover{border-color:var(--pink);box-shadow:0 0 20px #ff2bd633}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;padding:18px}.card{grid-column:span 4;background:linear-gradient(180deg,#111832dd,#0b1022dd);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 0 30px #0008}.card.wide{grid-column:span 8}.card.full{grid-column:span 12}.card h2{margin:0 0 12px;color:var(--cyan);font-size:20px}.card h3{margin:8px 0;color:#fff}.row{display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid #ffffff10;padding:9px 0}.muted{color:var(--muted)}.pill{display:inline-flex;align-items:center;gap:6px;padding:5px 9px;border:1px solid var(--line);border-radius:999px;color:var(--cyan);font-size:13px}.led{width:10px;height:10px;border-radius:50%;background:var(--warn);box-shadow:0 0 12px currentColor}.led.ok{background:var(--ok);color:var(--ok)}.led.bad{background:var(--bad);color:var(--bad)}button,input,textarea{font:inherit}button{background:linear-gradient(135deg,#122948,#3a1244);border:1px solid #22f7ff77;color:#fff;border-radius:12px;padding:10px 12px;cursor:pointer}button:hover{border-color:var(--pink);box-shadow:0 0 18px #ff2bd633}input,textarea{width:100%;background:#070b17;border:1px solid #22f7ff44;color:#fff;border-radius:12px;padding:10px}textarea{min-height:110px;resize:vertical}.controls{display:flex;flex-wrap:wrap;gap:10px}.screen{display:none}.screen.active{display:block}audio{width:100%;margin:8px 0 4px}.code{white-space:pre-wrap;background:#050811;border:1px solid #ffffff14;border-radius:14px;padding:12px;color:#d8f8ff;max-height:360px;overflow:auto}.small{font-size:12px}.danger{color:var(--bad)}.ok{color:var(--ok)}@media(max-width:900px){.card,.card.wide{grid-column:span 12}.grid{padding:12px}header{padding:18px 12px}}
</style>
</head>
<body>
<header><div class="wrap"><div class="brand"><div class="logo">666</div><div><h1>${cfg.botName}</h1><p>Vocard Sovereign Dashboard · Cyberstream Cockpit · kein Chatbot, sondern WebRadio Voice Stream Control</p></div></div><nav><button class="tab active" data-tab="overview">Overview</button><button class="tab" data-tab="stream">Stream</button><button class="tab" data-tab="shooter">Discord Shooter</button><button class="tab" data-tab="broadcast">Broadcast Relay</button><button class="tab" data-tab="admin">Admin/Auth</button><button class="tab" data-tab="vocard">Vocard Basis</button></nav></div></header>
<main class="wrap">
<section id="overview" class="screen active"><div class="grid"><div class="card"><h2>Worker</h2><div class="row"><span>Status</span><span class="pill"><span id="workerLed" class="led"></span><span id="workerState">prüfe...</span></span></div><div class="row"><span>Version</span><span>${cfg.version}</span></div><div class="row"><span>Rolle</span><span class="muted">API / Dashboard / Bridge</span></div></div><div class="card"><h2>Radio</h2><div class="row"><span>Stream</span><span class="pill"><span id="radioLed" class="led"></span><span id="radioState">prüfe...</span></span></div><div class="row"><span>Now Playing</span><span id="npState" class="muted">warte...</span></div><div class="row"><span>TuneIn</span><a style="color:var(--cyan)" href="${cfg.tuneInUrl}" target="_blank">öffnen</a></div></div><div class="card"><h2>Discord Bot</h2><div class="row"><span>Typ</span><span>Voice Radio Bot</span></div><div class="row"><span>Commands</span><span>/play /stop /volume</span></div><div class="row"><span>Volume</span><span>0–200 · Default 100</span></div></div><div class="card wide"><h2>Now Playing</h2><div id="nowPlayingBox" class="code">lade...</div></div><div class="card"><h2>Quick Actions</h2><div class="controls"><button onclick="refreshAll()">Status aktualisieren</button><button onclick="postNowPlaying()">NowPlaying posten</button><button onclick="showTab('stream')">Stream hören</button></div></div></div></section>
<section id="stream" class="screen"><div class="grid"><div class="card wide"><h2>Live Stream Preview</h2><audio controls src="${cfg.streamUrl}"></audio><div class="row"><span>Main Stream</span><span class="muted small">${cfg.streamUrl}</span></div><div class="row"><span>Fallback</span><span class="muted small">${cfg.fallbackStreamUrl}</span></div><p class="muted">Dieser Player ist nur Browser-Vorschau. Der Discord Voice Bot spielt separat im Voice Channel.</p></div><div class="card"><h2>Presets</h2><div class="controls"><button onclick="preset(1)">Preset 1</button><button onclick="preset(2)">Preset 2</button><button onclick="preset(3)">Preset 3</button><button onclick="preset(4)">Preset 4</button><button onclick="preset(5)">Preset 5</button></div><p class="muted small">Preset-Routen sind vorbereitet. Echte SonicPanel/AutoDJ-Schaltung bleibt geschützt.</p></div><div class="card full"><h2>Stream API Antwort</h2><div id="streamBox" class="code">-</div></div></div></section>
<section id="shooter" class="screen"><div class="grid"><div class="card"><h2>Discord Shooter Status</h2><button onclick="discordStatus()">Status prüfen</button><div id="discordStatusBox" class="code">-</div></div><div class="card wide"><h2>Message senden</h2><label class="muted small">Ziel</label><select id="discordTarget"><option value="main">Main / Hauptkanal</option><option value="url2">URL2 / Secondary</option><option value="url3">URL3 / Channel 1510363693622497400</option><option value="all">Alle konfigurierten Ziele</option></select><textarea id="messageText" placeholder="Nachricht für Discord Shooter..."></textarea><div class="controls"><button onclick="sendMessage()">Message senden</button><button onclick="manualBroadcast()">Manual Broadcast</button><button onclick="postNowPlaying()">NowPlaying posten</button><button onclick="sendDiscordTest()">Test senden</button></div><p class="muted small">Dashboard ruft nur diesen Worker auf. Webhook-Secrets bleiben serverseitig. URL3 ist Channel 1510363693622497400.</p></div></div></section>

<section id="broadcast" class="screen"><div class="grid"><div class="card"><h2>Renderer / Player Alert Status</h2><div class="controls"><button onclick="renderStatus()">Render Status</button><button onclick="playerAlertStatus()">Player Alert Status</button><button onclick="playerAlertCurrent()">Current</button><button onclick="playerAlertHistory()">History</button></div><div id="broadcastStatusBox" class="code">-</div></div><div class="card wide"><h2>Player Broadcast Relay</h2><textarea id="broadcastText" placeholder="Broadcast-Nachricht fuer Player Alert / Renderer Backend..."></textarea><div class="controls"><button onclick="sendPlayerAlert()">Player Alert senden</button></div><p class="muted small">Route aus WebRadio-Code uebernommen: Worker -> Render Backend -> KV -> Cache. Geschuetzt ueber Admin/Auth.</p></div></div></section>
<section id="admin" class="screen"><div class="grid"><div class="card wide"><h2>Admin / Gate</h2><p class="muted">Gate-Code oder Admin-Token wird nur im Browserfeld gehalten und als Header gesendet. Nicht in Repo oder Dashboard-Code speichern.</p><input id="gateCode" type="password" placeholder="Gate-Code oder Admin-Token eingeben"/><div class="controls"><button onclick="verifyAuth()">Auth prüfen</button><button onclick="authStatus()">Auth Status</button><button onclick="adminStatus()">Admin Status</button><button onclick="adminTest()">Protected Test</button><button onclick="clearGate()">Feld leeren</button></div><div id="authBox" class="code">-</div></div><div class="card"><h2>Schutzlogik</h2><div class="row"><span>Webhook im Frontend</span><span class="danger">Nein</span></div><div class="row"><span>Secrets sichtbar</span><span class="danger">Nein</span></div><div class="row"><span>Auth Worker</span><span class="muted">optional</span></div></div></div></section>
<section id="vocard" class="screen"><div class="grid"><div class="card full"><h2>Vocard Basis</h2><p>Die originale Vocard Dashboard-Struktur bleibt im Repo unter <b>Dashboard/Vocard-Dashboard-main</b> erhalten. Diese Cyberstream-Oberfläche ist die RadioBotAI-Erweiterung für Stream, Shooter, Status und Admin/Auth.</p><div class="row"><span>Dashboard Core</span><span>Vocard-Dashboard-main</span></div><div class="row"><span>Installer Core</span><span>Vocard-Installer-main</span></div><div class="row"><span>Bot Core</span><span>666-RadioBotAI</span></div><div class="row"><span>Worker Deploy</span><span>wrangler.toml → Arbeiter/src/index.js</span></div></div></div></section>
</main>
<script>
function $(id){return document.getElementById(id)}
function showTab(id){document.querySelectorAll('.screen').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));$(id).classList.add('active');const b=[...document.querySelectorAll('.tab')].find(x=>x.dataset.tab===id);if(b)b.classList.add('active')}
document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.tab)))
function gateHeaders(){const v=$('gateCode')?.value||'';return v?{'x-discord-gate-code':v,'x-admin-token':v}:{}}
async function api(path,opt={}){const r=await fetch(path,{...opt,headers:{'content-type':'application/json',...(opt.headers||{}),...gateHeaders()}});const t=await r.text();try{return JSON.parse(t)}catch(e){return {ok:r.ok,status:r.status,text:t}}}
function show(el,data){$(el).textContent=typeof data==='string'?data:JSON.stringify(data,null,2)}
function led(id,ok){const e=$(id);e.classList.remove('ok','bad');e.classList.add(ok?'ok':'bad')}

async function renderStatus(){show('broadcastStatusBox',await api('/render/status'))}
async function playerAlertStatus(){show('broadcastStatusBox',await api('/api/player-alert/status'))}
async function playerAlertCurrent(){show('broadcastStatusBox',await api('/api/player-alert/current'))}
async function playerAlertHistory(){show('broadcastStatusBox',await api('/api/player-alert/history'))}
async function sendPlayerAlert(){show('broadcastStatusBox',await api('/api/player-alert/send',{method:'POST',body:JSON.stringify({message:$('broadcastText')?.value||'',senderId:'radiobotai-dashboard',version:'v1.1.3'})}))}
async function refreshAll(){try{const s=await api('/status');show('nowPlayingBox',s);$('workerState').textContent=s.ok?'online':'error';led('workerLed',!!s.ok);$('radioState').textContent=s.radio?.healthOk?'online':'prüfen';led('radioLed',!!s.radio?.healthOk);$('npState').textContent=s.radio?.nowPlayingOk?'OK':'unbekannt'}catch(e){$('workerState').textContent='error';led('workerLed',false);show('nowPlayingBox',String(e))}}
async function loadNow(){show('nowPlayingBox',await api('/nowplaying'))}
async function loadStream(){show('streamBox',await api('/stream'))}
async function preset(n){show('streamBox',await api('/preset/'+n,{method:'POST',body:JSON.stringify({preset:n})}))}
async function discordStatus(){show('discordStatusBox',await api('/api/discord/status'))}
function selectedDiscordTarget(){return $('discordTarget') ? $('discordTarget').value : 'main'}
async function sendMessage(){show('discordStatusBox',await api('/api/discord/message',{method:'POST',body:JSON.stringify({target:selectedDiscordTarget(),message:$('messageText').value})}))}
async function manualBroadcast(){show('discordStatusBox',await api('/api/discord/manual',{method:'POST',body:JSON.stringify({target:selectedDiscordTarget(),message:$('messageText').value||'666 RadioBotAI Manual Broadcast'})}))}
async function postNowPlaying(){show('discordStatusBox',await api('/api/discord/nowplaying',{method:'POST',body:JSON.stringify({target:selectedDiscordTarget(),kind:'nowplaying'})}))}
async function sendDiscordTest(){show('discordStatusBox',await api('/api/discord/test',{method:'POST',body:JSON.stringify({target:selectedDiscordTarget(),message:'666 RadioBotAI Test aus dem Dashboard'})}))}
async function verifyAuth(){show('authBox',await api('/auth/verify',{method:'POST',body:JSON.stringify({gate:$('gateCode')?.value||''})}))}
async function authStatus(){show('authBox',await api('/auth/status'))}
async function adminStatus(){show('authBox',await api('/admin/status'))}
async function adminTest(){show('authBox',await api('/admin/protected-test',{method:'POST',body:JSON.stringify({gate:$('gateCode')?.value||''})}))}
function clearGate(){$('gateCode').value='';show('authBox','geleert')}
refreshAll();loadStream();
</script>
</body></html>`;
}

async function handleDashboard(env) {
  return html(dashboardHtml(env));
}

function getAutoDJConfig(env) {
  return {
    adminWorkerUrl: env.RADIO_ADMIN_WORKER_URL || env.MYIDJ_ADMIN_WORKER_URL || "https://666myidjstreamadmin.666soundsdesign-broadcaster.com",
    adminTokenConfigured: Boolean(env.RADIO_ADMIN_WORKER_TOKEN || env.ADMIN_TOKEN),
    skipConfigured: true,
    playlistConfigured: Boolean(env.RADIO_AUTODJ_PLAYLIST_SWITCH_URL),
    safeState: "playlist-switch-hold-until-confirmed-sonicpanel-request"
  };
}

function adminWorkerHeaders(env) {
  const token = env.RADIO_ADMIN_WORKER_TOKEN || env.ADMIN_TOKEN || "";
  const headers = { "content-type": "application/json" };
  if (token) {
    headers["authorization"] = `Bearer ${token}`;
    headers["x-admin-token"] = token;
  }
  return headers;
}

async function proxyAdminWorker(path, request, env, fallbackBody = {}) {
  const cfg = getAutoDJConfig(env);
  if (!cfg.adminWorkerUrl) return json({ ok: false, error: "RADIO_ADMIN_WORKER_URL_MISSING" }, 501);

  let body = fallbackBody;
  if (request.method !== "GET") {
    try { body = await request.json(); } catch (_) { body = fallbackBody; }
  }

  const target = cfg.adminWorkerUrl.replace(/\/$/, "") + path;
  try {
    const res = await fetch(target, {
      method: "POST",
      headers: adminWorkerHeaders(env),
      body: JSON.stringify({ source: "666radiobotai-main-worker", ...body }),
      cache: "no-store"
    });
    const textBody = await res.text();
    let data = null;
    try { data = textBody ? JSON.parse(textBody) : null; } catch (_) {}
    return json({
      ok: res.ok,
      proxied: true,
      targetWorker: cfg.adminWorkerUrl,
      status: res.status,
      data: data || textBody.slice(0, 1200)
    }, res.ok ? 200 : 502);
  } catch (error) {
    return json({ ok: false, proxied: true, error: String(error?.message || error) }, 502);
  }
}

async function handleAutoDJ(request, env, pathname) {
  const cfg = getAutoDJConfig(env);

  if (pathname === "/radio/autodj/status") {
    return json({
      ok: true,
      module: "autodj-control",
      version: "v1.2.2-audit-split-real-skip",
      skip: "GO",
      playlist: cfg.playlistConfigured ? "CONFIGURED_UNTESTED" : "HOLD_NO_CONFIRMED_SONICPANEL_ENDPOINT",
      adminWorkerUrlConfigured: Boolean(cfg.adminWorkerUrl),
      adminTokenConfigured: cfg.adminTokenConfigured,
      noListenerSpikeGuard: "ACTIVE_SKIP_ONLY_VIA_ADMIN_WORKER"
    });
  }

  if (pathname === "/radio/autodj/skip" || pathname === "/api/radio/skip" || pathname === "/autodj/skip") {
    if (request.method !== "POST") return json({ ok: false, error: "METHOD_NOT_ALLOWED_USE_POST" }, 405);
    const body = await requestBody(request);
    const auth = await verifyAdmin(request, env, body);
    if (!auth.ok) return json({ ok: false, error: "UNAUTHORIZED", auth: publicAuthStatus(env) }, 401);
    return proxyAdminWorker("/admin/autodj/skip", request, env, { action: "skip", ...body });
  }

  if (pathname === "/radio/autodj/playlist" || pathname === "/radio/autodj/playlist-switch" || pathname === "/autodj/playlist-switch") {
    if (!cfg.playlistConfigured) {
      return json({
        ok: false,
        action: "playlist-switch",
        error: "PLAYLIST_SWITCH_HOLD",
        message: "Kein Tricksen: SonicPanel Playlist On-the-Fly bleibt deaktiviert, bis ein echter stabiler SonicPanel-Request bekannt ist."
      }, 501);
    }
    if (request.method !== "POST") return json({ ok: false, error: "METHOD_NOT_ALLOWED_USE_POST" }, 405);
    const body = await requestBody(request);
    const auth = await verifyAdmin(request, env, body);
    if (!auth.ok) return json({ ok: false, error: "UNAUTHORIZED", auth: publicAuthStatus(env) }, 401);
    return proxyAdminWorker("/admin/autodj/playlist-switch", request, env, { action: "playlist-switch", ...body });
  }

  return null;
}

function notFound(pathname) {
  return json({ ok: false, error: "NOT_FOUND", path: pathname }, 404);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname.replace(/\/+$/, "") || "/";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: JSON_HEADERS });
    }

    if (pathname === "/") return handleRoot(env);
    if (pathname === "/health") return handleHealth(env);
    if (pathname === "/status") return handleStatus(env);
    if (pathname === "/nowplaying") return handleNowPlaying(env);
    if (pathname === "/stream") return handleStream(env);
    if (pathname === "/dashboard") return handleDashboard(env);
    if (pathname === "/config/public") return json({ ok: true, config: getPublicConfig(env) });
    if (pathname === "/auth/status") return handleAuthStatus(env);
    if (pathname === "/auth/verify") return handleAuthVerify(request, env);
    if (pathname === "/admin/status") return handleAdminStatus(request, env);
    if (pathname === "/admin/protected-test") return handleAdminProtectedTest(request, env);

    const playerAlertResponse = await handlePlayerAlert(request, env);
    if (playerAlertResponse) return playerAlertResponse;

    if (pathname === "/api/discord/status") return handleDiscordStatus(env);
    if (pathname === "/api/discord/debug") return handleDiscordDebug(env);
    if (pathname === "/api/discord/manual" && request.method === "POST") return directDiscordShooter(request, env, "manual");
    if (pathname === "/api/discord/message" && request.method === "POST") return directDiscordShooter(request, env, "message");
    if (pathname === "/api/discord/nowplaying" && request.method === "POST") return directDiscordShooter(request, env, "nowplaying");
    if (pathname === "/api/discord/test" && request.method === "POST") return directDiscordShooter(request, env, "test");

    if (["/radio/autodj/status", "/radio/autodj/skip", "/api/radio/skip", "/autodj/skip", "/radio/autodj/playlist", "/radio/autodj/playlist-switch", "/autodj/playlist-switch"].includes(pathname)) {
      const autodjResponse = await handleAutoDJ(request, env, pathname);
      if (autodjResponse) return autodjResponse;
    }

    const presetMatch = pathname.match(/^\/preset\/([1-5])$/);
    if (presetMatch) return handlePreset(request, env, presetMatch[1]);

    return notFound(pathname);
  }
};
