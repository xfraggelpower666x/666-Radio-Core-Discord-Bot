/**
 * 666RadioCoreDJ | src/utils/redact.js
 * Erstellt: 2026-06-03
 * Geändert: 2026-06-03
 * Zweck: Secrets aus Logs und Discord-Antworten entfernen.
 */
function redact(value) {
  if (value === undefined || value === null) return value;
  let output = String(value);

  const patterns = [
    /([?&](?:pass|password|token|auth|key)=)[^&\s]+/gi,
    /(Bearer\s+)[A-Za-z0-9._~+/=-]+/gi,
    /(Basic\s+)[A-Za-z0-9._~+/=-]+/gi
  ];

  for (const pattern of patterns) {
    output = output.replace(pattern, '$1[REDACTED]');
  }

  return output;
}

module.exports = { redact };
