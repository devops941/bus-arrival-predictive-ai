import { test } from 'node:test';
import assert from 'node:assert/strict';

// Test utils pure logic
function formatMinutes(mins) {
  if (mins === undefined || mins === null || isNaN(mins)) return '0.0 min';
  const sign = mins > 0 ? '+' : '';
  return `${sign}${mins.toFixed(1)} min`;
}

function getDelayCategory(delayMinutes) {
  if (delayMinutes < -1) return 'early';
  if (delayMinutes <= 2) return 'ontime';
  if (delayMinutes <= 5) return 'minor';
  return 'major';
}

function getReliabilityProps(tier) {
  const t = (tier || '').toUpperCase();
  if (t === 'HIGH') {
    return { label: 'High Confidence', score: 92 };
  }
  if (t === 'MEDIUM') {
    return { label: 'Moderate Confidence', score: 68 };
  }
  return { label: 'Low Confidence', score: 40 };
}

test('formatMinutes formats positive, zero, and negative values', () => {
  assert.equal(formatMinutes(3.24), '+3.2 min');
  assert.equal(formatMinutes(0), '0.0 min');
  assert.equal(formatMinutes(-1.5), '-1.5 min');
  assert.equal(formatMinutes(null), '0.0 min');
});

test('getDelayCategory categorizes early, ontime, minor, and major delays', () => {
  assert.equal(getDelayCategory(-2.0), 'early');
  assert.equal(getDelayCategory(0.5), 'ontime');
  assert.equal(getDelayCategory(2.0), 'ontime');
  assert.equal(getDelayCategory(3.5), 'minor');
  assert.equal(getDelayCategory(5.0), 'minor');
  assert.equal(getDelayCategory(6.2), 'major');
});

test('getReliabilityProps scores HIGH, MEDIUM, LOW', () => {
  assert.equal(getReliabilityProps('HIGH').score, 92);
  assert.equal(getReliabilityProps('medium').score, 68);
  assert.equal(getReliabilityProps('LOW').score, 40);
  assert.equal(getReliabilityProps(undefined).score, 40);
});
