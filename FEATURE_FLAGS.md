# Feature Flags

MapMyStandards now exposes product-level feature flags so unfinished intelligence systems can ship safely.

## Available flags

| Flag key | Product name |
| --- | --- |
| `standards_graph` | StandardsGraph™ |
| `evidence_mapper` | EvidenceMapper™ |
| `evidence_trust_score` | EvidenceTrust Score™ |
| `gap_risk_predictor` | GapRisk Predictor™ |
| `crosswalkx` | CrosswalkX™ |
| `citeguard` | CiteGuard™ |

## Backend configuration

* Flags are read from the `FEATURE_FLAGS` environment variable as JSON, for example:
  ```bash
  FEATURE_FLAGS='{"standards_graph": true, "citeguard": false}'
  ```
* In production environments, all flags default to off unless the variable is explicitly set.
* The FastAPI settings object exposes `settings.is_feature_enabled("flag")` for guards.
* A public endpoint at `GET /api/v1/feature-flags` returns the current flag state for frontend gating.

## Frontend usage

* `web/js/intelligence-stubs.js` loads the flag payload and hides UI sections for disabled capabilities.
* `web/ai-readiness-suite.html` shows placeholder data for each module, fed by stub API responses.

## Testing

* Backend smoke tests: `pytest tests/test_intelligence_showcase.py`
* Frontend smoke tests: `cd web && npm run test:e2e`

These guardrails let staging environments exercise the full suite while production stays opt-in.
