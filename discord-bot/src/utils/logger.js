/**
 * 666RadioCoreDJ | src/utils/logger.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Einheitliches Logging mit Secret-Redaction.
 */
const { redact } = require('./redact');

function stamp() {
  return new Date().toISOString();
}

function write(level, message, meta) {
  const base = `[${stamp()}] [${level.toUpperCase()}] ${redact(message)}`;
  if (meta) {
    console.log(base, redact(JSON.stringify(meta)));
  } else {
    console.log(base);
  }
}

module.exports = {
  info: (message, meta) => write('info', message, meta),
  warn: (message, meta) => write('warn', message, meta),
  error: (message, meta) => write('error', message, meta),
  debug: (message, meta) => {
    if ((process.env.LOG_LEVEL || 'info') === 'debug') write('debug', message, meta);
  }
};
