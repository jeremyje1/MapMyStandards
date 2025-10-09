const test = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const METRICS_SCRIPT_PATH = path.resolve('web/js/metrics-store.js');
const METRICS_SOURCE = readFileSync(METRICS_SCRIPT_PATH, 'utf8');

function createStorage(initial = {}) {
  const store = new Map(Object.entries(initial));
  return {
    getItem(key) {
      return store.get(key) ?? null;
    },
    setItem(key, value) {
      store.set(key, String(value));
    },
    removeItem(key) {
      store.delete(key);
    },
    clear() {
      store.clear();
    },
  };
}

function bootstrapStore({
  metricsPayload,
  evidencePayload,
  gapPayload,
  apiBase = 'https://api.mapmystandards.ai',
} = {}) {
  const responses = {
    '/dashboard/metrics': metricsPayload ?? {
      core_metrics: {
        documents_analyzed: 5,
        standards_mapped: 12,
        total_standards: 24,
      },
      performance_metrics: {
        coverage_percentage: 78.4,
        compliance_score: 81.3,
      },
      account_info: {
        institution_name: 'Test University',
      },
    },
    '/standards/evidence-map': evidencePayload ?? {
      counts: {
        documents: 4,
        standards_mapped: 12,
        total_standards: 24,
      },
      coverage_percentage: 78.4,
      standards: [
        { standard_id: 'HLC.1.A', avg_confidence: 0.82 },
        { standard_id: 'HLC.1.B', avg_confidence: 0.9 },
        { standard_id: 'HLC.1.C', avg_confidence: 0.61 },
      ],
    },
    '/gaps/analysis': gapPayload ?? {
      gap_analysis: {
        total_gaps: 3,
        high_risk: 1,
        medium_risk: 1,
        low_risk: 1,
      },
    },
  };

  const fetchHits = {};

  function makeResponse(body) {
    const jsonString = JSON.stringify(body ?? {});
    return {
      ok: true,
      status: 200,
      text: async () => jsonString,
      json: async () => body ?? {},
    };
  }

  const context = {
    window: {},
    document: { location: { href: 'https://platform.mapmystandards.ai/dashboard.html' } },
    location: { hostname: 'platform.mapmystandards.ai' },
    API_BASE: apiBase,
    localStorage: createStorage(),
    sessionStorage: createStorage(),
    console,
    fetch(url) {
      const key = Object.keys(responses).find((pattern) => url.includes(pattern));
      if (!key) {
        throw new Error(`Unhandled fetch call for ${url}`);
      }
      fetchHits[key] = (fetchHits[key] || 0) + 1;
      return Promise.resolve(makeResponse(responses[key]));
    },
  };

  context.window = context;
  context.window.window = context.window;
  context.window.location = { hostname: 'platform.mapmystandards.ai' };
  context.window.localStorage = context.localStorage;
  context.window.sessionStorage = context.sessionStorage;
  context.window.API_BASE = apiBase;
  context.window.fetch = context.fetch.bind(context);

  vm.createContext(context);
  vm.runInContext(METRICS_SOURCE, context);

  const store = context.window.A3EMetricsStore;
  assert.ok(store, 'A3EMetricsStore should be defined');
  store.reset();

  return { store, fetchHits };
}

test('ensure caches metrics, evidence map, and gap analysis within TTL', async () => {
  const { store, fetchHits } = bootstrapStore();

  const snapshotA = await store.ensure({ includeEvidenceMap: true, includeGapAnalysis: true });
  assert.equal(snapshotA.coreMetrics.documents_analyzed, 5);

  const snapshotB = await store.ensure({ includeEvidenceMap: true, includeGapAnalysis: true });
  assert.equal(snapshotB.coreMetrics.documents_analyzed, 5);

  assert.deepEqual(fetchHits, {
    '/dashboard/metrics': 1,
    '/standards/evidence-map': 1,
    '/gaps/analysis': 1,
  });
});

test('snapshot exposes inferred evidence stats with high confidence counts', async () => {
  const evidencePayload = {
    counts: {
      documents: 4,
      standards_mapped: 6,
      total_standards: 12,
    },
    coverage_percentage: 62.5,
    standards: [
      { standard_id: 'HLC.1.A', avg_confidence: 0.81 },
      { standard_id: 'HLC.1.B', avg_confidence: 0.76 },
      { standard_id: 'HLC.1.C', avg_confidence: 0.4 },
      { standard_id: 'HLC.1.D', avg_confidence: 0.95 },
    ],
  };

  const { store } = bootstrapStore({ evidencePayload });

  await store.ensure({ includeEvidenceMap: true });
  const snapshot = store.snapshot();

  assert.equal(snapshot.evidenceStats.mappedCount, 12);
  assert.equal(snapshot.evidenceStats.totalStandards, 24);
  assert.equal(snapshot.evidenceStats.coveragePercentage, 78.4);
  assert.equal(snapshot.evidenceStats.highConfidenceCount, 3);
});
