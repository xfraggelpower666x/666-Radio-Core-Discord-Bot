/**
 * 666RadioCoreDJ | scripts/local-audit.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Einfacher lokaler Projekt-Audit ohne externe Dependencies.
 * Änderung v1.3.0: Pause/Resume/Volume/Preset-Kommandos und Secret-Scan erweitert.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const required = [
  'index.js',
  'package.json',
  '.env.example',
  'src/index.js',
  'src/config.js',
  'src/radio/radioController.js',
  'src/radio/icyMetadataReader.js',
  'src/radio/streamHealthMonitor.js',
  'src/radio/adapters/sonicPanelAdapter.js',
  'src/radio/adapters/shoutcastAdapter.js',
  'src/voice/voiceRelay.js',
  'src/utils/track.js',
  'src/discord/commands.js',
  'src/discord/panel.js',
  'src/discord/replies.js',
  'scripts/register-commands.js',
  'README.md',
  'docs/SETUP.md',
  'docs/CHANGELOG.md',
  'docs/AUDIT.md'
];

let failed = false;
for (const file of required) {
  const full = path.join(root, file);
  if (!fs.existsSync(full)) {
    console.error(`FEHLT: ${file}`);
    failed = true;
  } else {
    console.log(`OK: ${file}`);
  }
}

const forbiddenPatterns = [
  /DISCORD_TOKEN=\s*(mfa\.|[A-Za-z0-9_\-.]{40,})/i,
  /SONICPANEL_DJ_PASS=\s*(?!PASTE_)[^\s#]+/i
];

const scanTargets = [
  '.env.example',
  'README.md',
  'docs/SETUP.md',
  'docs/CHANGELOG.md',
  'docs/AUDIT.md',
  'src/config.js',
  'src/index.js',
  'src/voice/voiceRelay.js',
  'src/radio/icyMetadataReader.js',
  'src/radio/streamHealthMonitor.js',
  'src/utils/track.js'
];

for (const file of scanTargets) {
  const full = path.join(root, file);
  if (!fs.existsSync(full)) continue;
  const content = fs.readFileSync(full, 'utf8');
  for (const pattern of forbiddenPatterns) {
    if (pattern.test(content)) {
      console.error(`BLOCKER: mögliches Secret in ${file} gefunden.`);
      failed = true;
    }
  }
}

const commandsFile = fs.readFileSync(path.join(root, 'src/discord/commands.js'), 'utf8');
for (const commandName of ["setName('play')", "setName('pause')", "setName('resume')", "setName('stop')", "setName('volume')", "setName('radio')"]) {
  if (!commandsFile.includes(commandName)) {
    console.error(`FEHLT: Slash Command ${commandName}`);
    failed = true;
  }
}

const voiceFile = fs.readFileSync(path.join(root, 'src/voice/voiceRelay.js'), 'utf8');
for (const marker of ['pauseFromInteraction', 'resumeFromInteraction', 'setVolumeFromInteraction', 'resetVolumeFromInteraction', 'presetByInput', 'IcyMetadataReader', 'StreamHealthMonitor', 'sendLogMessage']) {
  if (!voiceFile.includes(marker)) {
    console.error(`FEHLT: Voice-Funktion ${marker}`);
    failed = true;
  }
}

const envExample = fs.readFileSync(path.join(root, '.env.example'), 'utf8');
for (const envName of ['RADIO_LOG_CHANNEL_ID', 'STREAM_HEALTH_INTERVAL_SECONDS', 'STREAM_HEALTH_TIMEOUT_SECONDS']) {
  if (!envExample.includes(envName)) {
    console.error(`FEHLT: Env-Platzhalter ${envName}`);
    failed = true;
  }
}

if (failed) process.exit(1);
console.log('AUDIT PASS: Struktur vollständig, Voice-Presets/Pause/Resume/Volume, ICY-Metadata, Health-Monitoring und Log-Channel-Support vorhanden, keine bekannten Secrets in öffentlichen Dateien.');
