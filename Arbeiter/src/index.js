// ============================================================
// 666 RadioBotAI — Vocard Sovereign Dashboard Worker
// Version: v1.1.0
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
  "access-control-allow-headers": "content-type, authorization, x-admin-token, x-discord-gate-code"
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
    version: env.PUBLIC_VERSION || "v1.1.0",
    role: env.PUBLIC_WORKER_ROLE || "RadioBotAI API / Vocard Dashboard Bridge",
    webradioBaseUrl: base,
    streamUrl: env.PUBLIC_MAIN_STREAM_URL || `${base}/stream`,
    fallbackStreamUrl: env.PUBLIC_FALLBACK_STREAM_URL || `${base}/fallback-stream`,
    nowPlayingUrl: env.PUBLIC_NOWPLAYING_URL || `${base}/api/nowplaying`,
    healthUrl: env.PUBLIC_HEALTH_URL || `${base}/health`,
    tuneInUrl: env.PUBLIC_TUNEIN_URL || "https://tunein.com/radio/s357001",
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
      "/auth/verify",
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

async function verifyAdmin(request, env) {
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

  const verifyUrl = env.ADMIN_AUTH_VERIFY_URL || "";
  if (verifyUrl && auth) {
    const result = await safeFetchJson(verifyUrl, {
      method: "GET",
      headers: { authorization: auth }
    });
    if (result.ok && (result.data?.ok || result.data?.authorized || result.data?.valid)) {
      return { ok: true, method: "admin-auth-worker" };
    }
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
  return json({
    ok: true,
    action: "PRESET_REQUEST_RECEIVED",
    preset: presetId,
    note: "Preset endpoint prepared. Real SonicPanel/AutoDJ switch must be connected through protected control logic later.",
    timestamp: new Date().toISOString()
  });
}

async function handleAuthVerify(request, env) {
  const result = await verifyAdmin(request, env);
  return json({
    ok: result.ok,
    authenticated: result.ok,
    method: result.method,
    timestamp: new Date().toISOString()
  }, result.ok ? 200 : 401);
}

async function handleDiscordStatus(env) {
  const url = env.DISCORD_SHOOTER_STATUS_URL || `${env.PUBLIC_WEBRADIO_BASE_URL || "https://webradio.666soundsdesign-broadcaster.com"}/api/discord/status`;
  const upstream = await safeFetchJson(url);
  return json({
    ok: true,
    localBridge: "ready",
    upstreamConfigured: !!url,
    upstreamStatus: upstream,
    secrets: {
      discordAdminToken: !!env.DISCORD_ADMIN_TOKEN,
      discordGateCode: !!env.DISCORD_GATE_CODE,
      adminAuthVerifyUrl: !!env.ADMIN_AUTH_VERIFY_URL,
      shooterManualUrl: !!env.DISCORD_SHOOTER_MANUAL_URL,
      shooterMessageUrl: !!env.DISCORD_SHOOTER_MESSAGE_URL,
      shooterNowPlayingUrl: !!env.DISCORD_SHOOTER_NOWPLAYING_URL
    },
    note: "No secret values are exposed."
  });
}

async function handleDiscordDebug(env) {
  return json({
    ok: true,
    addon: "RadioBotAI Dashboard Shooter Bridge",
    mode: "bridge-to-existing-webradio-shooter-if-configured",
    secrets: {
      DISCORD_ADMIN_TOKEN: !!env.DISCORD_ADMIN_TOKEN,
      DISCORD_GATE_CODE: !!env.DISCORD_GATE_CODE,
      ADMIN_AUTH_VERIFY_URL: !!env.ADMIN_AUTH_VERIFY_URL,
      DISCORD_SHOOTER_STATUS_URL: !!env.DISCORD_SHOOTER_STATUS_URL,
      DISCORD_SHOOTER_MANUAL_URL: !!env.DISCORD_SHOOTER_MANUAL_URL,
      DISCORD_SHOOTER_MESSAGE_URL: !!env.DISCORD_SHOOTER_MESSAGE_URL,
      DISCORD_SHOOTER_NOWPLAYING_URL: !!env.DISCORD_SHOOTER_NOWPLAYING_URL
    }
  });
}

async function proxyShooter(request, env, kind) {
  const auth = await verifyAdmin(request, env);
  if (!auth.ok) {
    return json({ ok: false, error: "UNAUTHORIZED", note: "Admin token, gate code or auth worker verification required." }, 401);
  }

  const base = env.PUBLIC_WEBRADIO_BASE_URL || "https://webradio.666soundsdesign-broadcaster.com";
  const urls = {
    manual: env.DISCORD_SHOOTER_MANUAL_URL || `${base}/api/discord/manual`,
    message: env.DISCORD_SHOOTER_MESSAGE_URL || `${base}/api/discord/message`,
    nowplaying: env.DISCORD_SHOOTER_NOWPLAYING_URL || `${base}/api/discord/nowplaying`
  };
  const target = urls[kind];
  if (!target) {
    return json({ ok: false, error: "SHOOTER_TARGET_NOT_CONFIGURED", kind }, 500);
  }

  let body = {};
  try { body = await request.json(); } catch (_) {}
  body.source = body.source || "666radiobotai-dashboard";
  body.bridge = "666radiobotai-worker";

  const upstream = await safeFetchJson(target, {
    method: "POST",
    headers: forwardHeaders(request, env),
    body: JSON.stringify(body)
  });

  return json({
    ok: upstream.ok,
    kind,
    targetConfigured: true,
    upstream,
    timestamp: new Date().toISOString()
  }, upstream.ok ? 200 : 502);
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
<header><div class="wrap"><div class="brand"><div class="logo">666</div><div><h1>${cfg.botName}</h1><p>Vocard Sovereign Dashboard · Cyberstream Cockpit · kein Chatbot, sondern WebRadio Voice Stream Control</p></div></div><nav><button class="tab active" data-tab="overview">Overview</button><button class="tab" data-tab="stream">Stream</button><button class="tab" data-tab="shooter">Discord Shooter</button><button class="tab" data-tab="admin">Admin/Auth</button><button class="tab" data-tab="vocard">Vocard Basis</button></nav></div></header>
<main class="wrap">
<section id="overview" class="screen active"><div class="grid"><div class="card"><h2>Worker</h2><div class="row"><span>Status</span><span class="pill"><span id="workerLed" class="led"></span><span id="workerState">prüfe...</span></span></div><div class="row"><span>Version</span><span>${cfg.version}</span></div><div class="row"><span>Rolle</span><span class="muted">API / Dashboard / Bridge</span></div></div><div class="card"><h2>Radio</h2><div class="row"><span>Stream</span><span class="pill"><span id="radioLed" class="led"></span><span id="radioState">prüfe...</span></span></div><div class="row"><span>Now Playing</span><span id="npState" class="muted">warte...</span></div><div class="row"><span>TuneIn</span><a style="color:var(--cyan)" href="${cfg.tuneInUrl}" target="_blank">öffnen</a></div></div><div class="card"><h2>Discord Bot</h2><div class="row"><span>Typ</span><span>Voice Radio Bot</span></div><div class="row"><span>Commands</span><span>/play /stop /volume</span></div><div class="row"><span>Volume</span><span>0–200 · Default 100</span></div></div><div class="card wide"><h2>Now Playing</h2><div id="nowPlayingBox" class="code">lade...</div></div><div class="card"><h2>Quick Actions</h2><div class="controls"><button onclick="refreshAll()">Status aktualisieren</button><button onclick="postNowPlaying()">NowPlaying posten</button><button onclick="showTab('stream')">Stream hören</button></div></div></div></section>
<section id="stream" class="screen"><div class="grid"><div class="card wide"><h2>Live Stream Preview</h2><audio controls src="${cfg.streamUrl}"></audio><div class="row"><span>Main Stream</span><span class="muted small">${cfg.streamUrl}</span></div><div class="row"><span>Fallback</span><span class="muted small">${cfg.fallbackStreamUrl}</span></div><p class="muted">Dieser Player ist nur Browser-Vorschau. Der Discord Voice Bot spielt separat im Voice Channel.</p></div><div class="card"><h2>Presets</h2><div class="controls"><button onclick="preset(1)">Preset 1</button><button onclick="preset(2)">Preset 2</button><button onclick="preset(3)">Preset 3</button><button onclick="preset(4)">Preset 4</button><button onclick="preset(5)">Preset 5</button></div><p class="muted small">Preset-Routen sind vorbereitet. Echte SonicPanel/AutoDJ-Schaltung bleibt geschützt.</p></div><div class="card full"><h2>Stream API Antwort</h2><div id="streamBox" class="code">-</div></div></div></section>
<section id="shooter" class="screen"><div class="grid"><div class="card"><h2>Discord Shooter Status</h2><button onclick="discordStatus()">Status prüfen</button><div id="discordStatusBox" class="code">-</div></div><div class="card wide"><h2>Message senden</h2><textarea id="messageText" placeholder="Nachricht für Discord Shooter..."></textarea><div class="controls"><button onclick="sendMessage()">Message senden</button><button onclick="manualBroadcast()">Manual Broadcast</button><button onclick="postNowPlaying()">NowPlaying posten</button></div><p class="muted small">Dashboard ruft nur Worker-Routen auf. Webhook-Secrets bleiben serverseitig.</p></div></div></section>
<section id="admin" class="screen"><div class="grid"><div class="card wide"><h2>Admin / Gate</h2><p class="muted">Gate-Code oder Admin-Token wird nur im Browserfeld gehalten und als Header gesendet. Nicht in Repo oder Dashboard-Code speichern.</p><input id="gateCode" type="password" placeholder="Gate-Code oder Admin-Token eingeben"/><div class="controls"><button onclick="verifyAuth()">Auth prüfen</button><button onclick="clearGate()">Feld leeren</button></div><div id="authBox" class="code">-</div></div><div class="card"><h2>Schutzlogik</h2><div class="row"><span>Webhook im Frontend</span><span class="danger">Nein</span></div><div class="row"><span>Secrets sichtbar</span><span class="danger">Nein</span></div><div class="row"><span>Auth Worker</span><span class="muted">optional</span></div></div></div></section>
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
async function refreshAll(){try{const s=await api('/status');show('nowPlayingBox',s);$('workerState').textContent=s.ok?'online':'error';led('workerLed',!!s.ok);$('radioState').textContent=s.radio?.healthOk?'online':'prüfen';led('radioLed',!!s.radio?.healthOk);$('npState').textContent=s.radio?.nowPlayingOk?'OK':'unbekannt'}catch(e){$('workerState').textContent='error';led('workerLed',false);show('nowPlayingBox',String(e))}}
async function loadNow(){show('nowPlayingBox',await api('/nowplaying'))}
async function loadStream(){show('streamBox',await api('/stream'))}
async function preset(n){show('streamBox',await api('/preset/'+n,{method:'POST',body:JSON.stringify({preset:n})}))}
async function discordStatus(){show('discordStatusBox',await api('/api/discord/status'))}
async function sendMessage(){show('discordStatusBox',await api('/api/discord/message',{method:'POST',body:JSON.stringify({message:$('messageText').value})}))}
async function manualBroadcast(){show('discordStatusBox',await api('/api/discord/manual',{method:'POST',body:JSON.stringify({message:$('messageText').value||'666 RadioBotAI Manual Broadcast'})}))}
async function postNowPlaying(){show('discordStatusBox',await api('/api/discord/nowplaying',{method:'POST',body:JSON.stringify({kind:'nowplaying'})}))}
async function verifyAuth(){show('authBox',await api('/auth/verify'))}
function clearGate(){$('gateCode').value='';show('authBox','geleert')}
refreshAll();loadStream();
</script>
</body></html>`;
}

async function handleDashboard(env) {
  return html(dashboardHtml(env));
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
    if (pathname === "/auth/verify") return handleAuthVerify(request, env);

    if (pathname === "/api/discord/status") return handleDiscordStatus(env);
    if (pathname === "/api/discord/debug") return handleDiscordDebug(env);
    if (pathname === "/api/discord/manual" && request.method === "POST") return proxyShooter(request, env, "manual");
    if (pathname === "/api/discord/message" && request.method === "POST") return proxyShooter(request, env, "message");
    if (pathname === "/api/discord/nowplaying" && request.method === "POST") return proxyShooter(request, env, "nowplaying");

    const presetMatch = pathname.match(/^\/preset\/([1-5])$/);
    if (presetMatch) return handlePreset(request, env, presetMatch[1]);

    return notFound(pathname);
  }
};
