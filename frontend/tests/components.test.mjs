import { test, describe } from 'node:test';
import assert from 'node:assert/strict';

// 1. Semantic Status Badges & Reliability
describe('Semantic Status Formatting', () => {
  function getDelayCategory(delayMinutes) {
    if (delayMinutes < -1) return 'early';
    if (delayMinutes <= 2) return 'ontime';
    if (delayMinutes <= 5) return 'minor';
    return 'major';
  }

  function getReliabilityTier(score) {
    if (score >= 80) return 'HIGH';
    if (score >= 60) return 'MEDIUM';
    return 'LOW';
  }

  test('categorizes delay threshold boundaries correctly', () => {
    assert.equal(getDelayCategory(-5.0), 'early');
    assert.equal(getDelayCategory(-1.0), 'ontime');
    assert.equal(getDelayCategory(0.0), 'ontime');
    assert.equal(getDelayCategory(2.0), 'ontime');
    assert.equal(getDelayCategory(2.1), 'minor');
    assert.equal(getDelayCategory(5.0), 'minor');
    assert.equal(getDelayCategory(5.1), 'major');
    assert.equal(getDelayCategory(25.0), 'major');
  });

  test('evaluates reliability confidence scores', () => {
    assert.equal(getReliabilityTier(95), 'HIGH');
    assert.equal(getReliabilityTier(80), 'HIGH');
    assert.equal(getReliabilityTier(79), 'MEDIUM');
    assert.equal(getReliabilityTier(60), 'MEDIUM');
    assert.equal(getReliabilityTier(59), 'LOW');
    assert.equal(getReliabilityTier(20), 'LOW');
  });
});

// 2. Model Performance Leaderboard Sorting
describe('Model Registry Leaderboard', () => {
  const models = [
    { id: 'm1', name: 'Baseline Mean', metrics: { mae: 2.15, rmse: 2.80 } },
    { id: 'm2', name: 'Ridge Regressor', metrics: { mae: 1.62, rmse: 2.10 } },
    { id: 'm3', name: 'Quantile Gradient Boosting', metrics: { mae: 1.42, rmse: 1.90 } },
    { id: 'm4', name: 'Random Forest', metrics: { mae: 1.55, rmse: 2.05 } },
  ];

  test('sorts models ascending by MAE (lower is better)', () => {
    const sorted = [...models].sort((a, b) => a.metrics.mae - b.metrics.mae);
    assert.equal(sorted[0].name, 'Quantile Gradient Boosting');
    assert.equal(sorted[1].name, 'Random Forest');
    assert.equal(sorted[2].name, 'Ridge Regressor');
    assert.equal(sorted[3].name, 'Baseline Mean');
  });

  test('correctly evaluates improvement over baseline', () => {
    const baselineMae = 2.15;
    const gbMae = 1.42;
    const improvement = ((baselineMae - gbMae) / baselineMae) * 100;
    assert.ok(improvement > 30.0); // > 30% error reduction
  });
});

// 3. Role Access Control Guard
describe('Role-Based Route Guards', () => {
  function canAccessModule(userRole, allowedRoles) {
    if (!allowedRoles || allowedRoles.length === 0) return true;
    return allowedRoles.includes(userRole);
  }

  test('passenger cannot access analyst or admin views', () => {
    assert.equal(canAccessModule('passenger', ['analyst', 'admin']), false);
    assert.equal(canAccessModule('passenger', ['admin']), false);
    assert.equal(canAccessModule('passenger', ['passenger', 'analyst', 'admin']), true);
  });

  test('analyst can access ML views but not admin panel', () => {
    assert.equal(canAccessModule('analyst', ['analyst', 'admin']), true);
    assert.equal(canAccessModule('analyst', ['admin']), false);
  });

  test('admin has full access across all routes', () => {
    assert.equal(canAccessModule('admin', ['admin']), true);
    assert.equal(canAccessModule('admin', ['analyst', 'admin']), true);
    assert.equal(canAccessModule('admin', []), true);
  });
});

// 4. GTFS Static Column Header Translation
describe('GTFS Static Column Translator', () => {
  function mapGtfsRoute(raw) {
    return {
      route_no: raw.route_short_name || raw.route_id,
      name: raw.route_long_name || 'Express Corridor',
      color_hex: raw.route_color || '1D4ED8',
    };
  }

  test('translates GTFS routes.txt row to internal Route schema', () => {
    const rawGtfs = {
      route_id: 'R-101',
      agency_id: 'AGY',
      route_short_name: '101',
      route_long_name: 'Airport Express Corridor',
      route_color: '1D4ED8',
    };
    const mapped = mapGtfsRoute(rawGtfs);
    assert.equal(mapped.route_no, '101');
    assert.equal(mapped.name, 'Airport Express Corridor');
    assert.equal(mapped.color_hex, '1D4ED8');
  });
});
