// ============================================================
// 666SOUNDsDESIGn — Scriptable Multi-Repo GitHub Uploader GUI
// v3.7 RADIOBOTAI ONE UPLOADER FINAL
//
// Basis:
// - abgeleitet aus deinem v3.3 SAFE ROOT REPLACE Skript
//
// Ziel:
// - variable Repo-Profile
// - RadioBotAI bereits voreingestellt
// - du musst im Normalfall nur den GitHub-Token speichern
//
// Standard-Profil:
// Owner:  xfraggelpower666x
// Repo:   666RadioBotAI
// Branch: 666RadioBotAI
// Prefix: leer / Repo-Root
//
// Modi:
// 1) ORDNER hochladen / ergänzen
//    - Single Commit
//    - keine Löschung
//    - keine Mirror-Logik
//
// 2) RADIOBOTAI ROOT ersetzen / bereinigen
//    - lokaler Ordner = GitHub Repo Inhalt
//    - alte GitHub-Dateien, die lokal fehlen, werden gelöscht
//    - nur nach Vorschau + Sicherheitsbestätigung
//
// 3) Cloudflare Worker testen
//    - /health
//    - /status
//    - /dashboard
//
// Sicherheit:
// - GitHub Token lokal im iPhone-Keychain
// - Secrets werden nicht ausgegeben
// - echte .env / .dev.vars / Tokens / Logs / ZIPs werden ignoriert
// - Replace-Modus funktioniert nur mit leerem Prefix
// - RadioBotAI Root-Check prüft wrangler.toml + Worker-Main
// ============================================================
//
// v3.5 HARD PROTECT PATCH:
// - Arbeiter/, Dashboard/, Discord-Bot/, Render/, Docs/ und .github/
//   werden im Replace-Modus niemals automatisch gelöscht.
// - Wenn lokale ZIP falsch ist, wird ergänzt/aktualisiert, aber kritische
//   bestehende Repo-Struktur bleibt geschützt.
// - Für 666RadioBotAI gilt: main Worker bleibt Arbeiter/src/index.js.
//
const APP = {
  name: "666 RadioBotAI GitHub Uploader",
  version: "v3.7 RADIOBOTAI ONE UPLOADER FINAL",

  // Neue Keys, damit alte WebRadio-Uploader-Einstellungen nicht versehentlich überschrieben werden.
  keyToken: "S666_RADIOBOTAI_GITHUB_TOKEN",
  keyOwner: "S666_RADIOBOTAI_GITHUB_OWNER",
  keyRepo: "S666_RADIOBOTAI_GITHUB_REPO",
  keyBranch: "S666_RADIOBOTAI_GITHUB_BRANCH",
  keyPrefix: "S666_RADIOBOTAI_GITHUB_TARGET_PREFIX",
  keyBatch: "S666_RADIOBOTAI_GITHUB_BATCH_SIZE",
  keyDelay: "S666_RADIOBOTAI_GITHUB_DELAY_MS",
  keyProfile: "S666_RADIOBOTAI_REPO_PROFILE",

  logFile: "666_radiobotai_github_uploader_v34_log.json",
  checkpointFile: "666_radiobotai_github_uploader_v34_checkpoint.json"
};

const REPO_PROFILES = {
  radiobotai: {
    label: "666RadioBotAI — eigener Worker/Bot",
    owner: "xfraggelpower666x",
    repo: "666RadioBotAI",
    branch: "666RadioBotAI",
    prefix: "",
    rootType: "radiobotai",
    workerBaseUrl: "https://666radiobotai.666soundsdesign-broadcaster.com",
    description: "Eigene RadioBotAI Repo mit Cloudflare Worker 666radiobotai."
  },

  radioCoreCodex: {
    label: "666-Radio-Core-Discord-Bot — Codex",
    owner: "xfraggelpower666x",
    repo: "666-Radio-Core-Discord-Bot",
    branch: "Codex",
    prefix: "",
    rootType: "radioCore",
    workerBaseUrl: "https://666myidjshoutcaststream.666soundsdesign-broadcaster.com",
    description: "RadioCore / Codex Repo aus älteren Handoffs."
  },

  webradio: {
    label: "WebRadio-666SOUNDsDESIGn — produktives Radio",
    owner: "xfraggelpower666x",
    repo: "WebRadio-666SOUNDsDESIGn",
    branch: "WebRadio-666SOUNDsDESIGn",
    prefix: "",
    rootType: "webradio",
    workerBaseUrl: "https://webradio.666soundsdesign-broadcaster.com",
    description: "Produktive WebRadio Repo mit Player, Worker und bestehendem Discord-Shooter."
  }
};

const DEFAULT_PROFILE_KEY = "radiobotai";

// ------------------------------------------------------------
// v3.7 RADIOBOTAI ONE UPLOADER FINAL
// Erlaubte Zweit-Worker innerhalb derselben Repo.
// Diese Pfade sind KEINE Wrapper-/Build-Ordner, sondern genehmigte Worker.
// ------------------------------------------------------------
const RADIOBOTAI_ALLOWED_SECONDARY_WORKER_ROOTS = [
  "Workers/666myidjstreamadmin"
];

function isAllowedSecondaryWorkerRoot(repoPath) {
  const c = clean(repoPath);
  return RADIOBOTAI_ALLOWED_SECONDARY_WORKER_ROOTS.includes(c);
}

function isInsideAllowedSecondaryWorkerRoot(repoPath) {
  const c = clean(repoPath);
  return RADIOBOTAI_ALLOWED_SECONDARY_WORKER_ROOTS.some(root => c === root || c.startsWith(root + "/"));
}


const fmLocal = FileManager.local();
const fmCloud = FileManager.iCloud();
const docs = fmCloud.documentsDirectory();
const logPath = fmCloud.joinPath(docs, APP.logFile);
const checkpointPath = fmCloud.joinPath(docs, APP.checkpointFile);

// ------------------------------------------------------------
// KEYCHAIN / SETTINGS
// ------------------------------------------------------------

function kget(k, f = "") {
  try {
    if (Keychain.contains(k)) return Keychain.get(k);
  } catch (e) {}
  return f;
}

function kset(k, v) {
  Keychain.set(k, String(v ?? "").trim());
}

function selectedProfileKey() {
  const saved = kget(APP.keyProfile, DEFAULT_PROFILE_KEY);
  return REPO_PROFILES[saved] ? saved : DEFAULT_PROFILE_KEY;
}

function selectedProfile() {
  return REPO_PROFILES[selectedProfileKey()];
}

function token() { return kget(APP.keyToken); }
function owner() { return kget(APP.keyOwner, selectedProfile().owner); }
function repo() { return kget(APP.keyRepo, selectedProfile().repo); }
function branch() { return kget(APP.keyBranch, selectedProfile().branch); }
function prefix() { return clean(kget(APP.keyPrefix, selectedProfile().prefix)); }
function rootType() { return selectedProfile().rootType || "radiobotai"; }
function workerBaseUrl() { return selectedProfile().workerBaseUrl || ""; }
function batchSize() { return Math.max(1, Number(kget(APP.keyBatch, "5")) || 5); }
function delayMs() { return Math.max(0, Number(kget(APP.keyDelay, "2500")) || 2500); }

// ------------------------------------------------------------
// BASICS
// ------------------------------------------------------------

function stamp() {
  return new Date().toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

function clean(v) {
  return String(v || "")
    .replace(/^\/+/, "")
    .replace(/\/+/g, "/")
    .replace(/\.\./g, "")
    .trim();
}

function baseName(p) {
  return String(p || "").split("/").filter(Boolean).pop() || "";
}

function join(...parts) {
  return parts.filter(Boolean).join("/").replace(/\/+/g, "/");
}

function rel(root, file) {
  let r = String(root).replace(/\/+$/, "");
  let f = String(file);
  if (f.startsWith(r)) f = f.slice(r.length);
  return clean(f);
}

function lowerName(path) {
  return baseName(path).toLowerCase();
}

// ------------------------------------------------------------
// SKIP / SECRET PROTECTION
// ------------------------------------------------------------

function skip(path) {
  const n = baseName(path);
  const lower = lowerName(path);

  if (!n) return true;

  // System / Mac / Git / Node
  if (n === ".DS_Store") return true;
  if (n === "__MACOSX") return true;
  if (n === ".git") return true;
  if (n === "node_modules") return true;
  if (n === ".wrangler") return true;
  if (n === ".cache") return true;
  if (n === "dist") return true;
  if (n === "build") return true;
  if (n === "coverage") return true;
  if (n.startsWith("._")) return true;

  // Env / Secrets
  if (n === ".env") return true;
  if (n.startsWith(".env.")) return true;
  if (n === ".dev.vars") return true;
  if (lower.includes("secret") && !lower.endsWith(".example")) return true;
  if (lower.includes("token") && !lower.endsWith(".example")) return true;
  if (lower.includes("password") && !lower.endsWith(".example")) return true;
  if (lower.includes("private") && !lower.endsWith(".example")) return true;
  if (lower.endsWith(".pem")) return true;
  if (lower.endsWith(".key")) return true;
  if (lower.endsWith(".token")) return true;
  if (lower === "secrets.json") return true;
  if (lower === "config.private.json") return true;

  // Archives / logs
  if (lower.endsWith(".zip")) return true;
  if (lower.endsWith(".7z")) return true;
  if (lower.endsWith(".rar")) return true;
  if (lower.endsWith(".tar")) return true;
  if (lower.endsWith(".gz")) return true;
  if (lower.endsWith(".log")) return true;
  if (lower.startsWith("npm-debug.log")) return true;
  if (lower.startsWith("yarn-error.log")) return true;

  return false;
}

function isDangerousRepoPath(p) {
  const c = clean(p);
  const n = baseName(c);
  const lower = n.toLowerCase();

  if (!c) return true;
  if (c === ".git" || c.startsWith(".git/")) return true;
  if (c === "node_modules" || c.startsWith("node_modules/")) return true;
  if (c === ".wrangler" || c.startsWith(".wrangler/")) return true;
  if (c === ".env" || c.startsWith(".env.")) return true;
  if (c === ".dev.vars") return true;
  if (lower.includes("secret") && !lower.endsWith(".example")) return true;
  if (lower.includes("token") && !lower.endsWith(".example")) return true;
  if (lower.includes("password") && !lower.endsWith(".example")) return true;
  if (lower.endsWith(".pem") || lower.endsWith(".key") || lower.endsWith(".token")) return true;

  // ------------------------------------------------------------
  // v3.7 RADIOBOTAI ONE UPLOADER FINAL
  // Diese bestehenden Repo-Hauptbereiche dürfen im Root-Replace
  // NIEMALS automatisch gelöscht werden.
  // Grund: Scriptable Replace darf keine vorhandene Dashboard-/Bot-/
  // Render-/Worker-Struktur zerstören, wenn die lokale ZIP falsch ist.
  // ------------------------------------------------------------
  const protectedRoots = [
    "Arbeiter",
    "Dashboard",
    "Discord-Bot",
    "Render",
    "Docs",
    "Workers/666myidjstreamadmin",
    ".github"
  ];

  for (const root of protectedRoots) {
    if (c === root || c.startsWith(root + "/")) return true;
  }

  // Auch wichtige Root-Dateien nicht automatisch löschen.
  const protectedFiles = [
    "wrangler.toml",
    "package.json",
    ".gitignore",
    "README.md"
  ];
  if (protectedFiles.includes(c)) return true;

  return false;
}

// ------------------------------------------------------------
// LOG / UI
// ------------------------------------------------------------

function log(type, msg, extra = {}) {
  let items = [];
  try {
    if (fmCloud.fileExists(logPath)) items = JSON.parse(fmCloud.readString(logPath));
    if (!Array.isArray(items)) items = [];
  } catch (e) {
    items = [];
  }

  items.push({ time: stamp(), type, msg, extra });

  try {
    fmCloud.writeString(logPath, JSON.stringify(items.slice(-400), null, 2));
  } catch (e) {}

  console.log(`${stamp()}: ${type}: ${msg}`);
  if (extra && Object.keys(extra).length) console.log(JSON.stringify(extra));
}

async function alertBox(title, msg) {
  const a = new Alert();
  a.title = title;
  a.message = msg;
  a.addAction("OK");
  await a.presentAlert();
}

async function inputBox(title, msg, placeholder = "", value = "", secure = false) {
  const a = new Alert();
  a.title = title;
  a.message = msg;

  if (secure && a.addSecureTextField) a.addSecureTextField(placeholder, value);
  else a.addTextField(placeholder, value);

  a.addAction("Speichern");
  a.addCancelAction("Abbrechen");

  const r = await a.presentAlert();
  if (r !== 0) return null;
  return a.textFieldValue(0);
}

async function confirmText(title, msg, requiredText) {
  const a = new Alert();
  a.title = title;
  a.message = msg + `\n\nZum Bestätigen exakt eingeben:\n${requiredText}`;
  a.addTextField(requiredText, "");
  a.addDestructiveAction("Ausführen");
  a.addCancelAction("Abbrechen");

  const r = await a.presentAlert();
  if (r !== 0) return false;

  return String(a.textFieldValue(0) || "").trim() === requiredText;
}

async function menu(title, msg, actions, cancel = "Schließen") {
  const a = new Alert();
  a.title = title;
  a.message = msg;
  actions.forEach(x => a.addAction(x));
  a.addCancelAction(cancel);
  return await a.presentSheet();
}

function sleep(ms) {
  return new Promise(resolve => Timer.schedule(ms / 1000, false, resolve));
}

// ------------------------------------------------------------
// GITHUB API
// ------------------------------------------------------------

function ghHeaders() {
  if (!token()) throw new Error("GitHub Token fehlt.");

  return {
    "Authorization": "Bearer " + token(),
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "666-RadioBotAI-GitHub-Uploader-v37"
  };
}

async function gh(method, url, body = null, tries = 5) {
  let lastErr = null;

  for (let attempt = 1; attempt <= tries; attempt++) {
    try {
      const req = new Request(url);
      req.method = method;
      req.headers = ghHeaders();
      req.timeoutInterval = 150;

      if (body !== null) {
        req.headers["Content-Type"] = "application/json";
        req.body = JSON.stringify(body);
      }

      const text = await req.loadString();
      const status = req.response ? req.response.statusCode : 0;

      let data = null;
      try { data = text ? JSON.parse(text) : null; } catch (e) {}

      if (status >= 200 && status < 300) return data || text;

      const msg = data && data.message ? data.message : text;
      throw new Error(`GitHub HTTP ${status}: ${msg}`);
    } catch (e) {
      lastErr = e;
      log("retry", `${method} Versuch ${attempt}/${tries} fehlgeschlagen`, {
        url,
        error: e.message
      });
      if (attempt < tries) await sleep(3000 * attempt);
    }
  }

  throw lastErr;
}

async function getRef() {
  return await gh("GET", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/ref/heads/${encodeURIComponent(branch())}`);
}

async function getCommit(sha) {
  return await gh("GET", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/commits/${sha}`);
}

async function getTreeRecursive(treeSha) {
  return await gh("GET", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/trees/${encodeURIComponent(treeSha)}?recursive=1`);
}

async function createBlob(base64) {
  const res = await gh("POST", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/blobs`, {
    content: base64,
    encoding: "base64"
  });
  return res.sha;
}

async function createTree(baseTreeSha, entries) {
  return await gh("POST", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/trees`, {
    base_tree: baseTreeSha,
    tree: entries
  });
}

async function createCommit(message, treeSha, parentSha) {
  return await gh("POST", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/commits`, {
    message,
    tree: treeSha,
    parents: [parentSha]
  });
}

async function updateBranch(commitSha) {
  return await gh("PATCH", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}/git/refs/heads/${encodeURIComponent(branch())}`, {
    sha: commitSha,
    force: false
  });
}

// ------------------------------------------------------------
// FILE SYSTEM
// ------------------------------------------------------------

async function waitCloud(path) {
  try {
    if (fmCloud.fileExists(path) && fmCloud.isFileDownloaded && !fmCloud.isFileDownloaded(path)) {
      await fmCloud.downloadFileFromiCloud(path);
    }
  } catch (e) {}
}

async function readData(path) {
  await waitCloud(path);

  let data = null;
  try { data = fmLocal.read(path); } catch (e) {}
  if (!data) {
    try { data = fmCloud.read(path); } catch (e) {}
  }

  if (!data || typeof data.toBase64String !== "function") {
    throw new Error("Datei nicht lesbar: " + path);
  }

  return data;
}

async function pickFolder() {
  try {
    if (DocumentPicker.openFolder) return await DocumentPicker.openFolder();
  } catch (e) {
    log("picker", "openFolder failed", { error: e.message });
  }

  await alertBox("Ordnerauswahl", "Ordner in Dateien-App auswählen oder teilen und mit Scriptable öffnen.");

  try {
    const picked = await DocumentPicker.open(["public.folder", "public.directory", "public.item"]);
    return Array.isArray(picked) ? picked[0] : picked;
  } catch (e) {
    return null;
  }
}

function isDir(path) {
  try { return fmLocal.isDirectory(path); } catch (e) {}
  try { return fmCloud.isDirectory(path); } catch (e) {}
  return false;
}

function exists(path) {
  try { if (fmLocal.fileExists(path)) return true; } catch (e) {}
  try { if (fmCloud.fileExists(path)) return true; } catch (e) {}
  return false;
}

function list(path) {
  try { return fmLocal.listContents(path); } catch (e) {}
  try { return fmCloud.listContents(path); } catch (e) {}
  throw new Error("Ordner nicht lesbar: " + path);
}

function listFiles(root) {
  const out = [];

  function walk(dir) {
    for (const name of list(dir)) {
      const full = join(dir, name);
      if (skip(full)) continue;
      if (isDir(full)) walk(full);
      else out.push(full);
    }
  }

  walk(root);
  return out;
}

function scanRepoRoots(root) {
  const roots = [];

  function walk(dir) {
    if (isAllowedSecondaryWorkerRoot(clean(rel(root, dir)))) return;
    let flags = {
      indexHtml: false,
      workerJs: false,
      wranglerToml: false,
      wranglerJsonc: false,
      packageJson: false,
      arbeiter: false,
      discordBot: false,
      docs: false
    };

    for (const name of list(dir)) {
      if (skip(join(dir, name))) continue;

      if (name === "index.html") flags.indexHtml = true;
      if (name === "worker.js") flags.workerJs = true;
      if (name === "wrangler.toml") flags.wranglerToml = true;
      if (name === "wrangler.jsonc") flags.wranglerJsonc = true;
      if (name === "package.json") flags.packageJson = true;
      if (name === "Arbeiter" || name === "worker") flags.arbeiter = true;
      if (name === "Discord-Bot" || name === "discord-bot") flags.discordBot = true;
      if (name === "Docs" || name === "docs") flags.docs = true;
    }

    const looksLikeRoot =
      flags.indexHtml ||
      flags.workerJs ||
      flags.wranglerToml ||
      flags.wranglerJsonc ||
      flags.discordBot ||
      flags.arbeiter;

    if (looksLikeRoot) {
      roots.push({
        path: dir,
        flags,
        relative: clean(rel(root, dir)) || "/"
      });
    }

    for (const name of list(dir)) {
      const full = join(dir, name);
      if (skip(full)) continue;
      if (isDir(full)) walk(full);
    }
  }

  walk(root);
  return roots;
}

// ------------------------------------------------------------
// ROOT CHECKS
// ------------------------------------------------------------

function validateRadioBotAIRoot(folder, requireEmptyPrefix = false) {
  const errors = [];
  const warnings = [];

  const wranglerToml = join(folder, "wrangler.toml");
  const wranglerJsonc = join(folder, "wrangler.jsonc");

  const arbeiterIndex = join(folder, "Arbeiter/src/index.js");
  const arbeiterPackage = join(folder, "Arbeiter/package.json");

  const workerIndex = join(folder, "worker/src/index.js");
  const workerPackage = join(folder, "worker/package.json");

  const rootWorkerJs = join(folder, "worker.js");
  const rootPackage = join(folder, "package.json");

  const discordBotA = join(folder, "Discord-Bot");
  const discordBotB = join(folder, "discord-bot");
  const docsA = join(folder, "Docs");
  const docsB = join(folder, "docs");

  if (!exists(wranglerToml) && !exists(wranglerJsonc)) {
    errors.push("wrangler.toml oder wrangler.jsonc liegt nicht direkt im gewählten Repo-Root.");
  }

  const hasWorkerMain =
    exists(arbeiterIndex) ||
    exists(workerIndex) ||
    exists(rootWorkerJs);

  if (!hasWorkerMain) {
    errors.push("Kein Worker-Main gefunden. Erwartet: Arbeiter/src/index.js oder worker/src/index.js oder worker.js.");
  }

  const hasPackage =
    exists(arbeiterPackage) ||
    exists(workerPackage) ||
    exists(rootPackage);

  if (!hasPackage) {
    warnings.push("Kein package.json gefunden. Cloudflare kann trotzdem deployen, wenn Wrangler global/automatisch läuft, aber empfohlen ist package.json.");
  }

  if (!exists(discordBotA) && !exists(discordBotB)) {
    warnings.push("Kein Discord-Bot/ oder discord-bot/ Ordner gefunden. Für reinen Worker-Test okay, für finalen Bot-Stand prüfen.");
  }

  if (!exists(docsA) && !exists(docsB)) {
    warnings.push("Kein Docs/ oder docs/ Ordner gefunden. Änderungsberichte sollten in Docs/docs liegen.");
  }

  if (!exists(join(folder, ".env.example"))) {
    warnings.push(".env.example fehlt. Keine echten .env-Dateien hochladen, aber Beispiel-ENV ist empfohlen.");
  }

  if (requireEmptyPrefix && prefix()) {
    errors.push("Zielprefix muss im Replace-Modus leer sein.");
  }

  const roots = scanRepoRoots(folder);
  const unapprovedRoots = roots.filter(r => !isAllowedSecondaryWorkerRoot(clean(rel(folder, r.path || r.full || r.dir || r))));

  const badRoots = roots.filter(x =>
    x.relative !== "/" &&
    !isAllowedSecondaryWorkerRoot(x.relative) &&
    (
      x.flags.wranglerToml ||
      x.flags.wranglerJsonc ||
      (x.flags.indexHtml && x.flags.workerJs)
    )
  );

  if (badRoots.length) {
    errors.push(
      "Mehrere mögliche Repo-/Worker-Roots gefunden. Vermutlich Wrapper-/Build-Ordner im Upload-Ordner:\n" +
      badRoots.map(x => x.relative).slice(0, 8).join("\n")
    );
  }

  const files = listFiles(folder);
  const zipFiles = files.filter(f => /\.(zip|7z|rar|tar|gz)$/i.test(baseName(f)));
  if (zipFiles.length) {
    warnings.push("ZIP/Archiv-Dateien im Upload-Ordner gefunden. Diese werden ignoriert, sollten aber nicht im Repo liegen.");
  }

  return {
    ok: errors.length === 0,
    errors,
    warnings,
    roots,
    files
  };
}

function validateWebRadioRoot(folder, requireEmptyPrefix = false) {
  const errors = [];
  const warnings = [];

  const indexPath = join(folder, "index.html");
  const workerPath = join(folder, "worker.js");
  const cssPath = join(folder, "css");
  const jsPath = join(folder, "js");

  if (!exists(indexPath)) errors.push("index.html liegt nicht direkt im gewählten Ordner.");
  if (!exists(workerPath)) errors.push("worker.js liegt nicht direkt im gewählten Ordner.");
  if (!exists(cssPath) || !isDir(cssPath)) errors.push("css/ liegt nicht direkt im gewählten Ordner.");
  if (!exists(jsPath) || !isDir(jsPath)) errors.push("js/ liegt nicht direkt im gewählten Ordner.");

  if (requireEmptyPrefix && prefix()) {
    errors.push("Zielprefix muss im Replace-Modus leer sein.");
  }

  const roots = scanRepoRoots(folder);
  const badRoots = roots.filter(x => x.relative !== "/" && x.flags.indexHtml && x.flags.workerJs);

  if (badRoots.length) {
    errors.push(
      "Mehrere Repo-Roots gefunden. Vermutlich Wrapper-/Build-Ordner im Upload-Ordner:\n" +
      badRoots.map(x => x.relative).slice(0, 8).join("\n")
    );
  }

  const files = listFiles(folder);
  const zipFiles = files.filter(f => /\.(zip|7z|rar|tar|gz)$/i.test(baseName(f)));
  if (zipFiles.length) {
    warnings.push("ZIP/Archiv-Dateien im Upload-Ordner gefunden. Diese werden ignoriert, sollten aber nicht im Repo liegen.");
  }

  return {
    ok: errors.length === 0,
    errors,
    warnings,
    roots,
    files
  };
}

function validateRepoRoot(folder, requireEmptyPrefix = false) {
  if (rootType() === "webradio") return validateWebRadioRoot(folder, requireEmptyPrefix);
  return validateRadioBotAIRoot(folder, requireEmptyPrefix);
}

function formatCheckResult(check) {
  const lines = [];
  if (check.errors && check.errors.length) {
    lines.push("FEHLER:");
    lines.push(...check.errors.map(x => "- " + x));
    lines.push("");
  }
  if (check.warnings && check.warnings.length) {
    lines.push("HINWEISE:");
    lines.push(...check.warnings.map(x => "- " + x));
    lines.push("");
  }
  lines.push(`Dateien: ${(check.files || []).length}`);
  return lines.join("\n");
}

// ------------------------------------------------------------
// CHECKPOINTS
// ------------------------------------------------------------

function loadCheckpoint() {
  try {
    if (fmCloud.fileExists(checkpointPath)) {
      const data = JSON.parse(fmCloud.readString(checkpointPath));
      if (data && typeof data === "object") return data;
    }
  } catch (e) {}
  return null;
}

function saveCheckpoint(cp) {
  try {
    fmCloud.writeString(checkpointPath, JSON.stringify(cp, null, 2));
  } catch (e) {
    log("checkpoint_error", "Checkpoint konnte nicht gespeichert werden", { error: e.message });
  }
}

function clearCheckpoint() {
  try {
    if (fmCloud.fileExists(checkpointPath)) fmCloud.remove(checkpointPath);
  } catch (e) {}
}

function makeCheckpoint(folder, files, mode = "upload") {
  return {
    version: APP.version,
    profile: selectedProfileKey(),
    mode,
    created: stamp(),
    updated: stamp(),
    owner: owner(),
    repo: repo(),
    branch: branch(),
    prefix: prefix(),
    folder,
    total: files.length,
    blobs: {},
    lastFile: "",
    lastIndex: 0,
    phase: "created"
  };
}

function checkpointMatches(cp, folder, mode = "upload") {
  return cp &&
    cp.owner === owner() &&
    cp.repo === repo() &&
    cp.branch === branch() &&
    cp.prefix === prefix() &&
    cp.folder === folder &&
    cp.mode === mode;
}

async function buildBlobEntries(folder, files, cp) {
  let uploaded = 0;
  let reused = 0;

  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    const repoPath = clean(join(prefix(), rel(folder, file)));

    cp.lastIndex = i + 1;
    cp.lastFile = repoPath;
    cp.updated = stamp();

    if (cp.blobs[repoPath]) {
      reused++;
      log("reuse", `${i + 1}/${files.length}: ${repoPath}`, { sha: cp.blobs[repoPath] });
    } else {
      log("blob", `${i + 1}/${files.length}: ${repoPath}`);
      const data = await readData(file);
      const sha = await createBlob(data.toBase64String());
      cp.blobs[repoPath] = sha;
      uploaded++;
      log("blob_ok", `${i + 1}/${files.length}: ${repoPath}`, { sha });
    }

    saveCheckpoint(cp);

    if ((i + 1) % batchSize() === 0) {
      log("pause", `Batch-Pause nach ${i + 1}/${files.length}`, {
        uploaded,
        reused,
        delay: delayMs()
      });
      await sleep(delayMs());
    } else {
      await sleep(80);
    }
  }

  const entries = files.map(file => {
    const repoPath = clean(join(prefix(), rel(folder, file)));
    const sha = cp.blobs[repoPath];

    if (!sha) throw new Error("Checkpoint unvollständig für Datei: " + repoPath);

    return {
      path: repoPath,
      mode: "100644",
      type: "blob",
      sha
    };
  });

  return { entries, uploaded, reused };
}

async function prepareGitBase(cp) {
  cp.phase = "get_ref";
  cp.updated = stamp();
  saveCheckpoint(cp);

  const ref = await getRef();
  const parentSha = ref.object.sha;
  log("github", "REF OK", { parentSha });

  cp.phase = "get_commit";
  cp.parentSha = parentSha;
  cp.updated = stamp();
  saveCheckpoint(cp);

  const parentCommit = await getCommit(parentSha);
  const baseTreeSha = parentCommit.tree.sha;
  log("github", "BASE TREE OK", { baseTreeSha });

  cp.parentSha = parentSha;
  cp.baseTreeSha = baseTreeSha;
  cp.updated = stamp();
  saveCheckpoint(cp);

  return { parentSha, baseTreeSha };
}

// ------------------------------------------------------------
// CLOUDFLARE / WORKER TEST
// ------------------------------------------------------------

async function httpGetJsonOrText(url) {
  const req = new Request(url);
  req.method = "GET";
  req.timeoutInterval = 30;

  const text = await req.loadString();
  const status = req.response ? req.response.statusCode : 0;

  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch (e) {}

  return {
    ok: status >= 200 && status < 300,
    status,
    json,
    text: text ? String(text).slice(0, 1500) : ""
  };
}

async function testWorker(showAlert = true) {
  const base = workerBaseUrl();

  if (!base) {
    if (showAlert) await alertBox("Worker Test", "Für dieses Profil ist keine Worker-URL hinterlegt.");
    return { ok: false, reason: "missing_worker_url" };
  }

  const endpoints = ["/health", "/status", "/dashboard"];
  const results = [];

  for (const ep of endpoints) {
    const url = base.replace(/\/+$/, "") + ep;
    try {
      const res = await httpGetJsonOrText(url);
      results.push({
        endpoint: ep,
        url,
        ok: res.ok,
        status: res.status,
        body: res.json ? JSON.stringify(res.json).slice(0, 500) : res.text.slice(0, 500)
      });
    } catch (e) {
      results.push({
        endpoint: ep,
        url,
        ok: false,
        status: 0,
        error: e.message
      });
    }

    await sleep(600);
  }

  const allOk = results.some(x => x.endpoint === "/health" && x.ok);

  log("worker_test", allOk ? "Worker Health OK" : "Worker Health nicht OK", {
    base,
    results
  });

  if (showAlert) {
    const msg = results.map(x =>
      `${x.endpoint}\nStatus: ${x.status || "-"}\nOK: ${x.ok ? "JA" : "NEIN"}${x.error ? "\nFehler: " + x.error : ""}`
    ).join("\n\n");

    await alertBox(
      "Cloudflare Worker Test",
      `Profil: ${selectedProfile().label}\nWorker:\n${base}\n\n${msg}`
    );
  }

  return { ok: allOk, results };
}

async function waitAfterUploadAndTestWorker() {
  const choice = await menu(
    "Cloudflare Auto-Deploy",
    "Upload ist fertig. Cloudflare braucht oft etwas Zeit.\n\nJetzt Healthcheck versuchen?",
    ["30 Sekunden warten + testen", "Sofort testen", "Nicht testen"],
    "Abbrechen"
  );

  if (choice === -1 || choice === 2) return null;
  if (choice === 0) await sleep(30000);
  return await testWorker(true);
}

// ------------------------------------------------------------
// MODUS 1: APPEND ONLY
// ------------------------------------------------------------

async function uploadFolderAppendOnly() {
  const folder = await pickFolder();
  if (!folder) return;

  const rootCheck = validateRepoRoot(folder, false);
  if (!rootCheck.ok) {
    return await alertBox(
      "Root-Check fehlgeschlagen",
      "Der gewählte Ordner passt nicht zum aktuellen Profil.\n\n" +
      formatCheckResult(rootCheck) +
      "\n\nUpload wurde gestoppt."
    );
  }

  if (rootCheck.warnings && rootCheck.warnings.length) {
    const proceed = await menu(
      "Root-Check Hinweise",
      formatCheckResult(rootCheck) + "\n\nTrotz Hinweise fortfahren?",
      ["Fortfahren"],
      "Abbrechen"
    );
    if (proceed !== 0) return;
  }

  const files = rootCheck.files;
  if (!files.length) return await alertBox("Leer", "Keine Dateien gefunden.");

  let cp = loadCheckpoint();
  let resume = false;

  if (checkpointMatches(cp, folder, "upload")) {
    const done = Object.keys(cp.blobs || {}).length;
    const choice = await menu(
      "Checkpoint gefunden",
      `Es gibt einen alten Upload-Stand:\n\n${done}/${cp.total || files.length} Blobs vorhanden\nLetzte Datei:\n${cp.lastFile || "-"}\n\nFortsetzen oder neu starten?`,
      ["Fortsetzen", "Neu starten"],
      "Abbrechen"
    );

    if (choice === -1) return;
    if (choice === 0) resume = true;
    if (choice === 1) {
      clearCheckpoint();
      cp = null;
    }
  }

  if (!cp || !resume) cp = makeCheckpoint(folder, files, "upload");

  const ok = await menu(
    "ORDNER hochladen / ergänzen",
    `Modus: KEINE LÖSCHUNG\n\nProfil:\n${selectedProfile().label}\n\nOrdner:\n${folder}\n\nDateien: ${files.length}\nRepo: ${owner()}/${repo()}\nBranch: ${branch()}\nPrefix: ${prefix() || "/"}\nBatch: ${batchSize()}\nDelay: ${delayMs()} ms\n\nDieser Modus überschreibt/ergänzt nur. Alte Repo-Dateien bleiben erhalten.\n\nFortfahren?`,
    ["Upload starten"],
    "Abbrechen"
  );

  if (ok !== 0) return;

  const msg = await inputBox(
    "Commit Message",
    "Ein Commit für den ganzen Ordner.",
    "upload full folder",
    `upload: ${repo()} ${baseName(folder)}`
  );

  if (msg === null) return;

  try {
    log("start", "Append-only Ordnerupload", {
      folder,
      files: files.length,
      resume,
      profile: selectedProfileKey(),
      repo: `${owner()}/${repo()}`,
      branch: branch(),
      prefix: prefix() || "/"
    });

    const { parentSha, baseTreeSha } = await prepareGitBase(cp);

    cp.phase = "blobs";
    cp.updated = stamp();
    saveCheckpoint(cp);

    const blobResult = await buildBlobEntries(folder, files, cp);

    cp.phase = "tree";
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("tree", "TREE START", { entries: blobResult.entries.length, baseTreeSha });
    const tree = await createTree(baseTreeSha, blobResult.entries);
    log("tree", "TREE OK", { treeSha: tree.sha });

    cp.phase = "commit";
    cp.treeSha = tree.sha;
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("commit", "COMMIT START", { treeSha: tree.sha, parentSha });
    const commit = await createCommit(msg, tree.sha, parentSha);
    log("commit", "COMMIT OK", { commitSha: commit.sha });

    cp.phase = "branch";
    cp.commitSha = commit.sha;
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("branch", "BRANCH UPDATE START", { commitSha: commit.sha });
    await updateBranch(commit.sha);
    log("branch", "BRANCH UPDATE OK", { commitSha: commit.sha });

    cp.phase = "done";
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("done", "Append-only Upload fertig", {
      files: files.length,
      uploaded: blobResult.uploaded,
      reused: blobResult.reused,
      commit: commit.sha
    });

    clearCheckpoint();

    await alertBox(
      "Upload OK",
      `Modus: Keine Löschung\n\nDateien: ${files.length}\nNeu hochgeladen: ${blobResult.uploaded}\nWiederverwendet: ${blobResult.reused}\n\nCommit:\n${commit.sha}`
    );

    await waitAfterUploadAndTestWorker();
  } catch (e) {
    cp.phase = "error";
    cp.error = e.message;
    cp.errorStack = String(e.stack || "");
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("error", "Upload Fehler: " + e.message, {
      phase: cp.phase,
      lastIndex: cp.lastIndex,
      lastFile: cp.lastFile,
      error: e.message,
      stack: String(e.stack || "")
    });

    await alertBox(
      "Upload Fehler",
      `${e.message}\n\nStand gespeichert.\nBeim nächsten Start kannst du fortsetzen.\n\nLetzte Datei:\n${cp.lastIndex}/${cp.total}\n${cp.lastFile || "-"}`
    );
  }
}

// ------------------------------------------------------------
// MODUS 2: SAFE ROOT REPLACE / CONTROLLED MIRROR
// ------------------------------------------------------------

async function uploadFolderSafeRootReplace() {
  const folder = await pickFolder();
  if (!folder) return;

  const rootCheck = validateRepoRoot(folder, true);
  if (!rootCheck.ok) {
    return await alertBox(
      "Replace gestoppt",
      "Der gewählte Ordner ist kein sicherer Repo-Root für das aktuelle Profil.\n\n" +
      formatCheckResult(rootCheck) +
      "\n\nEs wurde NICHT hochgeladen und NICHT gelöscht."
    );
  }

  if (rootCheck.warnings && rootCheck.warnings.length) {
    const proceed = await menu(
      "Root-Check Hinweise",
      formatCheckResult(rootCheck) + "\n\nTrotz Hinweise fortfahren?",
      ["Fortfahren"],
      "Abbrechen"
    );
    if (proceed !== 0) return;
  }

  const files = rootCheck.files;
  if (!files.length) return await alertBox("Leer", "Keine Dateien gefunden.");

  const danger = await menu(
    "REPO-ROOT ersetzen / bereinigen",
    `ACHTUNG: Dieser Modus löscht GitHub-Dateien, die lokal nicht im gewählten Ordner existieren.\n\nProfil:\n${selectedProfile().label}\n\nOrdner:\n${folder}\n\nLokal: ${files.length} Dateien\nRepo: ${owner()}/${repo()}\nBranch: ${branch()}\nPrefix: /\n\nNur fortfahren, wenn dieser lokale Ordner wirklich der komplette Repo-Inhalt sein soll.`,
    ["Vorschau erstellen"],
    "Abbrechen"
  );

  if (danger !== 0) return;

  let cp = makeCheckpoint(folder, files, "replace");

  try {
    log("start", "Safe Root Replace Vorschau", {
      folder,
      files: files.length,
      profile: selectedProfileKey(),
      repo: `${owner()}/${repo()}`,
      branch: branch()
    });

    const { parentSha, baseTreeSha } = await prepareGitBase(cp);

    cp.phase = "get_remote_tree";
    cp.updated = stamp();
    saveCheckpoint(cp);

    const remote = await getTreeRecursive(baseTreeSha);
    const remoteFiles = (remote.tree || [])
      .filter(x => x.type === "blob")
      .map(x => clean(x.path))
      .filter(Boolean);

    const localRepoPaths = files.map(file => clean(rel(folder, file)));
    const localSet = {};
    localRepoPaths.forEach(p => localSet[p] = true);

    const rawDeletePaths = remoteFiles.filter(p => !localSet[p]);
    const protectedDeletes = rawDeletePaths.filter(p => isDangerousRepoPath(p));
    const deletePaths = rawDeletePaths.filter(p => !isDangerousRepoPath(p));

    const preview = [
      `PROFIL: ${selectedProfile().label}`,
      `REPO: ${owner()}/${repo()} @ ${branch()}`,
      "",
      `LOKAL: ${localRepoPaths.length} Dateien`,
      `GITHUB: ${remoteFiles.length} Dateien`,
      `WERDEN GELÖSCHT: ${deletePaths.length} Dateien`,
      `GESCHÜTZT / NICHT GELÖSCHT: ${protectedDeletes.length} Dateien`,
      "",
      "Beispiele Löschliste:",
      ...(deletePaths.slice(0, 30).map(p => "- " + p)),
      deletePaths.length > 30 ? `... und ${deletePaths.length - 30} weitere` : "",
      "",
      protectedDeletes.length ? "Geschützte Remote-Pfade bleiben erhalten:" : "",
      ...(protectedDeletes.slice(0, 12).map(p => "- " + p)),
      protectedDeletes.length > 12 ? `... und ${protectedDeletes.length - 12} weitere` : ""
    ].filter(Boolean).join("\n");

    const show = new Alert();
    show.title = "Replace Vorschau";
    show.message = preview.slice(0, 6500);
    show.addAction("Weiter");
    show.addCancelAction("Abbrechen");

    const showResult = await show.presentAlert();
    if (showResult !== 0) return;

    const required = rootType() === "webradio" ? "REPLACE WEBRADIO ROOT" : "REPLACE RADIOBOTAI ROOT";

    const confirmed = await confirmText(
      "Endgültige Bestätigung",
      `Repo-Root wird ersetzt.\n\nProfil:\n${selectedProfile().label}\n\nLokal: ${localRepoPaths.length}\nGitHub aktuell: ${remoteFiles.length}\nLöschungen: ${deletePaths.length}\nGeschützt nicht gelöscht: ${protectedDeletes.length}\n\nDieser Vorgang erzeugt EINEN Commit.`,
      required
    );

    if (!confirmed) {
      await alertBox("Abgebrochen", "Keine Änderung durchgeführt.");
      return;
    }

    const msg = await inputBox(
      "Commit Message",
      "Ein Commit für Root Replace / Bereinigung.",
      "safe root replace",
      `safe root replace: ${repo()} ${baseName(folder)}`
    );

    if (msg === null) return;

    cp.phase = "blobs";
    cp.updated = stamp();
    saveCheckpoint(cp);

    const blobResult = await buildBlobEntries(folder, files, cp);

    const deleteEntries = deletePaths.map(p => ({
      path: p,
      mode: "100644",
      type: "blob",
      sha: null
    }));

    const entries = blobResult.entries.concat(deleteEntries);

    cp.phase = "tree_replace";
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("tree", "REPLACE TREE START", {
      addOrUpdate: blobResult.entries.length,
      delete: deleteEntries.length,
      protectedDeletes: protectedDeletes.length,
      baseTreeSha
    });

    const tree = await createTree(baseTreeSha, entries);
    log("tree", "REPLACE TREE OK", { treeSha: tree.sha });

    cp.phase = "commit";
    cp.treeSha = tree.sha;
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("commit", "COMMIT START", { treeSha: tree.sha, parentSha });
    const commit = await createCommit(msg, tree.sha, parentSha);
    log("commit", "COMMIT OK", { commitSha: commit.sha });

    cp.phase = "branch";
    cp.commitSha = commit.sha;
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("branch", "BRANCH UPDATE START", { commitSha: commit.sha });
    await updateBranch(commit.sha);
    log("branch", "BRANCH UPDATE OK", { commitSha: commit.sha });

    cp.phase = "done";
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("done", "Safe Root Replace fertig", {
      localFiles: files.length,
      uploaded: blobResult.uploaded,
      reused: blobResult.reused,
      deleted: deleteEntries.length,
      protectedNotDeleted: protectedDeletes.length,
      commit: commit.sha
    });

    clearCheckpoint();

    await alertBox(
      "Root Replace OK",
      `Repo wurde an lokalen Ordner angepasst.\n\nLokal: ${files.length}\nNeu hochgeladen: ${blobResult.uploaded}\nWiederverwendet: ${blobResult.reused}\nGelöscht: ${deleteEntries.length}\nGeschützt nicht gelöscht: ${protectedDeletes.length}\n\nCommit:\n${commit.sha}`
    );

    await waitAfterUploadAndTestWorker();
  } catch (e) {
    cp.phase = "error";
    cp.error = e.message;
    cp.errorStack = String(e.stack || "");
    cp.updated = stamp();
    saveCheckpoint(cp);

    log("error", "Safe Root Replace Fehler: " + e.message, {
      phase: cp.phase,
      lastIndex: cp.lastIndex,
      lastFile: cp.lastFile,
      error: e.message,
      stack: String(e.stack || "")
    });

    await alertBox(
      "Replace Fehler",
      `${e.message}\n\nEs wurde ggf. vor dem Commit abgebrochen.\nCheckpoint wurde gespeichert.`
    );
  }
}

// ------------------------------------------------------------
// SETUP / PROFILE
// ------------------------------------------------------------

async function applyProfile(profileKey) {
  const p = REPO_PROFILES[profileKey];
  if (!p) return;

  kset(APP.keyProfile, profileKey);
  kset(APP.keyOwner, p.owner);
  kset(APP.keyRepo, p.repo);
  kset(APP.keyBranch, p.branch);
  kset(APP.keyPrefix, p.prefix);

  await alertBox(
    "Profil gesetzt",
    `${p.label}\n\nOwner: ${p.owner}\nRepo: ${p.repo}\nBranch: ${p.branch}\nPrefix: ${p.prefix || "/"}\n\nToken bleibt unverändert.`
  );
}

async function chooseProfile() {
  const keys = Object.keys(REPO_PROFILES);
  const labels = keys.map(k => {
    const active = k === selectedProfileKey() ? "✓ " : "";
    return active + REPO_PROFILES[k].label;
  });

  const r = await menu(
    "Repo-Profil wählen",
    "Wähle das Zielprofil. RadioBotAI ist der Standard.",
    labels,
    "Abbrechen"
  );

  if (r === -1) return;
  await applyProfile(keys[r]);
}

async function setup() {
  const o = await inputBox("Owner", "GitHub Owner", "xfraggelpower666x", owner());
  if (o === null) return;

  const r = await inputBox("Repo", "Repository", "666RadioBotAI", repo());
  if (r === null) return;

  const b = await inputBox("Branch", "Branch", "666RadioBotAI", branch());
  if (b === null) return;

  const p = await inputBox("Zielprefix", "Leer = Repo-Root. Replace-Modus funktioniert nur mit leerem Prefix.", "", prefix());
  if (p === null) return;

  const bs = await inputBox("Batch Size", "Empfehlung iPhone 13: 5 / iPhone 15: 10", "5", String(batchSize()));
  if (bs === null) return;

  const dm = await inputBox("Delay ms", "Empfehlung iPhone 13: 3000 / iPhone 15: 2000", "2500", String(delayMs()));
  if (dm === null) return;

  kset(APP.keyOwner, o);
  kset(APP.keyRepo, r);
  kset(APP.keyBranch, b);
  kset(APP.keyPrefix, clean(p));
  kset(APP.keyBatch, bs);
  kset(APP.keyDelay, dm);

  await alertBox("Gespeichert", "Einstellungen gespeichert.");
}

async function setToken() {
  const t = await inputBox("GitHub Token", "Token lokal im Keychain speichern. Es wird nicht angezeigt oder geloggt.", "github_pat_...", "", true);
  if (t === null) return;
  if (!t.trim()) return await alertBox("Leer", "Token nicht gespeichert.");

  kset(APP.keyToken, t);
  await alertBox("Gespeichert", "Token lokal gespeichert.");
}

async function testGitHub() {
  try {
    const res = await gh("GET", `https://api.github.com/repos/${encodeURIComponent(owner())}/${encodeURIComponent(repo())}`);
    await alertBox(
      "GitHub OK",
      `Repo erreichbar:\n${res.full_name || owner() + "/" + repo()}\n\nBranch:\n${branch()}\n\nProfil:\n${selectedProfile().label}`
    );
  } catch (e) {
    await alertBox("Fehler", e.message);
  }
}

async function status() {
  const cp = loadCheckpoint();

  await alertBox(
    APP.name,
    `${APP.version}\n\nProfil: ${selectedProfile().label}\nOwner: ${owner()}\nRepo: ${repo()}\nBranch: ${branch()}\nPrefix: ${prefix() || "/"}\nRoot-Typ: ${rootType()}\nWorker: ${workerBaseUrl() || "-"}\nBatch: ${batchSize()}\nDelay: ${delayMs()} ms\nToken: ${token() ? "gesetzt" : "fehlt"}\n\nModi:\n1. Upload/Ergänzen = löscht nichts\n2. Root ersetzen = löscht nach Vorschau\n\nCheckpoint: ${cp ? "vorhanden" : "keiner"}${cp ? `\nModus: ${cp.mode || "-"}\nPhase: ${cp.phase}\nStand: ${Object.keys(cp.blobs || {}).length}/${cp.total}\nLetzte Datei:\n${cp.lastFile || "-"}` : ""}`
  );
}

async function showLog() {
  let items = [];
  try {
    if (fmCloud.fileExists(logPath)) items = JSON.parse(fmCloud.readString(logPath));
  } catch (e) {}

  if (!Array.isArray(items) || !items.length) {
    return await alertBox("Log", "Leer.");
  }

  const text = items.slice(-70).reverse().map(x =>
    `${x.time}\n${x.type}: ${x.msg}\n${JSON.stringify(x.extra || {})}`
  ).join("\n\n────────────\n\n");

  const a = new Alert();
  a.title = "Log";
  a.message = text.slice(0, 7000);
  a.addAction("OK");
  a.addDestructiveAction("Log löschen");

  const r = await a.presentAlert();

  if (r === 1) {
    try { fmCloud.writeString(logPath, "[]"); } catch (e) {}
  }
}

async function clearSavedCheckpoint() {
  const r = await menu(
    "Checkpoint löschen",
    "Nur löschen, wenn du bewusst komplett neu starten willst.",
    ["Checkpoint löschen"],
    "Abbrechen"
  );

  if (r !== 0) return;

  clearCheckpoint();
  await alertBox("OK", "Checkpoint gelöscht.");
}

// ------------------------------------------------------------
// MAIN GUI
// ------------------------------------------------------------

async function main() {
  // Beim allerersten Start Profilwerte vorfüllen, damit nur Token nötig ist.
  if (!kget(APP.keyRepo, "")) {
    const p = selectedProfile();
    kset(APP.keyOwner, p.owner);
    kset(APP.keyRepo, p.repo);
    kset(APP.keyBranch, p.branch);
    kset(APP.keyPrefix, p.prefix);
    kset(APP.keyBatch, "5");
    kset(APP.keyDelay, "2500");
  }

  while (true) {
    const r = await menu(
      APP.name,
      `${APP.version}\n${owner()}/${repo()} @ ${branch()}\nProfil: ${selectedProfile().label}`,
      [
        "ORDNER hochladen / ergänzen",
        "RADIOBOTAI ROOT ersetzen / bereinigen",
        "GitHub Verbindung testen",
        "Cloudflare Worker testen",
        "Repo-Profil wählen",
        "Einstellungen",
        "Token speichern",
        "Status",
        "Log",
        "Checkpoint löschen"
      ],
      "Schließen"
    );

    if (r === -1) break;
    if (r === 0) await uploadFolderAppendOnly();
    if (r === 1) await uploadFolderSafeRootReplace();
    if (r === 2) await testGitHub();
    if (r === 3) await testWorker(true);
    if (r === 4) await chooseProfile();
    if (r === 5) await setup();
    if (r === 6) await setToken();
    if (r === 7) await status();
    if (r === 8) await showLog();
    if (r === 9) await clearSavedCheckpoint();
  }
}

await main();
