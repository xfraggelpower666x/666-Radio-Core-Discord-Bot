import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeTrackTitle, parseIcyMetadata } from '../src/utils/track.js';

test('parseIcyMetadata extracts quoted ICY pairs', () => {
  assert.deepEqual(
    parseIcyMetadata("StreamTitle='Artist - Title';StreamUrl='https://example.com';"),
    {
      StreamTitle: 'Artist - Title',
      StreamUrl: 'https://example.com'
    }
  );
});

test('normalizeTrackTitle trims whitespace and empty values', () => {
  assert.equal(normalizeTrackTitle('  Artist   -   Title  '), 'Artist - Title');
  assert.equal(normalizeTrackTitle('    '), null);
  assert.equal(normalizeTrackTitle(null), null);
});
