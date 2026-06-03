export function normalizeTrackTitle(title) {
  if (!title) return null;
  const cleaned = String(title).replace(/\s+/g, ' ').trim();
  return cleaned.length > 0 ? cleaned : null;
}

export function parseIcyMetadata(metadata) {
  const result = {};
  if (!metadata) return result;

  const pairs = String(metadata).matchAll(/([A-Za-z0-9_-]+)='([^']*)';/g);
  for (const match of pairs) {
    result[match[1]] = match[2];
  }

  return result;
}
