Where the live models live (by module)

StandardsGraph™ (standards knowledge graph)

Source of truth: Postgres on Railway (schema: standards, clauses, relations) + pgvector for embeddings.

Model calls: AWS Bedrock (Titan Embeddings) for chunk embeddings; OpenAI GPT-4.1-mini for relation extraction prompts.

Compute: Serverless workers (Vercel Edge for extraction, Railway job for bulk ETL).

Artifacts: Graph persisted as tables; denormalized standards_graph_edges.

EvidenceMapper™ (artifact → standards alignment)

Source of truth: S3 bucket (mms-artifacts) for files; artifacts table; artifact_chunks with vectors.

Model calls: Bedrock Claude 3.5 Sonnet (ranking/rationale) + embeddings via Titan; optional OpenAI rerank step (text-embedding-3-large or Cohere Rerank v3 if added later).

Compute: Chunk & embed pipeline as a Railway worker; alignment API in the FastAPI service (/api/evidence/map).

CrosswalkX™ (framework-to-framework mapping)

Source of truth: standards for both frameworks (e.g., SACS ↔ MSCHE) + crosswalk_edges table.

Model calls: GPT-4.1-mini for candidate mappings; deterministic post-filter using keyword/ontology overlap.

Compute: Batch job to pre-compute + on-demand refine endpoint.

GapRisk Predictor™ (coverage & risk scoring)

Source of truth: joins of evidence_links, crosswalk_edges, standards_graph_edges.

Model calls: None required for v1 (pure heuristic + calibrated weights); optional LLM critique for narratives.

Compute: Railway job recalculates nightly; API endpoint returns latest snapshot.

EvidenceTrust Score™ (provenance & quality)

Source of truth: artifacts metadata (author, date, system of record), artifact_lineage, confidence_signals.

Model calls: LLM only for explanation text; score is deterministic from signals (freshness, authorship, redundancy, citation density, original vs derivative).

Compute: Inline in EvidenceMapper pipeline + nightly recompute.

CiteGuard™ (citation & policy guardrails)

Source of truth: citations table + raw extract from artifacts.

Model calls: Small LLM (GPT-4o-mini) with strict JSON mode for detection; regex/AST checks to validate references.

Compute: Synchronous in upload/align flows; async retune for large docs.

Reference implementations & acceptance criteria (what we already have vs. missing)

Existing (in repos you shared):

MapMyStandards: API routes scaffolding, upload flows, dashboard, multiple ops docs and fix logs. Good backbone for wiring new services.

AI Readiness app: mature PDF/report generation patterns, policy pack library patterns that we can mirror for “rule packs” (accreditor rules).

Needed to ship v1:

Embeddings infra (pgvector enablement + migration).

S3 (or R2) artifact storage + signed URL utilities.

Chunker (PDF, DOCX, HTML) with page-level provenance.

Ranker/aligner service (LLM + vector search + rule filters).

Scoring functions for GapRisk & EvidenceTrust (deterministic).

Crosswalk builder (batch + refine).

CiteGuard checker (sync + report).

Data contracts (request/response payloads)
1) EvidenceMapper™

POST /api/evidence/map

// request
{
  "artifact_id": "uuid",
  "standard_set": "SACSCOC_2024",
  "top_k": 5,
  "threshold": 0.62,
  "explain": true
}
// response
{
  "artifact_id": "uuid",
  "matches": [
    {
      "standard_id": "SACS.8.2.a",
      "score": 0.83,
      "evidence_spans": [{"page": 3, "start": 120, "end": 280}],
      "rationale": "…only if explain=true",
      "evidence_trust": 0.74,
      "citations": [{"type": "page","value":3}]
    }
  ],
  "computed_at": "2025-10-10T13:00:00Z"
}

2) StandardsGraph™

POST /api/standards/ingest

{
  "standard_set": "SACSCOC_2024",
  "source_url": "https://…",
  "parse_mode": "html|pdf|markdown"
}


GET /api/standards/graph?standard_set=SACSCOC_2024

{
  "nodes": [{"id":"SACS.8.2.a","type":"clause","title":"…" }],
  "edges": [{"from":"SACS.8.2","to":"SACS.8.2.a","type":"subsumes"}]
}

3) CrosswalkX™

POST /api/crosswalk/build

{"from_set":"SACSCOC_2024","to_set":"MSCHE_2023","method":"batch|refine"}


GET /api/crosswalk?from=SACSCOC_2024&to=MSCHE_2023

{
  "pairs":[
    {"from":"SACS.8.2.a","to":"MSCHE.III.2","confidence":0.71, "rationale":"…"}
  ]
}

4) GapRisk Predictor™

GET /api/risk/coverage?standard_set=SACSCOC_2024

{
  "coverage": 0.64,
  "gaps": [
    {"standard_id":"SACS.6.1","gap_score":0.82, "drivers":["no recent artifacts","weak crosswalk support"]}
  ],
  "risk_index": 0.37,
  "recommendations": ["Upload most recent assessment plan for 6.1"]
}

5) EvidenceTrust Score™

POST /api/evidence/trust-score

{"artifact_id":"uuid"}


response

{
  "artifact_id":"uuid",
  "trust": 0.78,
  "signals": {
    "freshness": 0.9,
    "authenticity": 0.8,
    "redundancy": 0.6,
    "citation_density": 0.7
  },
  "explanation": "Latest copy signed by VPAA; corroborated in annual report."
}

6) CiteGuard™

POST /api/citations/validate

{"artifact_id":"uuid","style":"APA7|Chicago|Internal"}


response

{
  "artifact_id":"uuid",
  "status":"pass|warn|fail",
  "issues":[{"code":"MISSING_CITATION","where":"page 5","hint":"…"}]
}

New infrastructure dependencies (choose defaults now)

Database: Railway Postgres with pgvector (CREATE EXTENSION IF NOT EXISTS vector;).

Object storage: AWS S3 bucket mms-artifacts + presigned URL helpers.

Embedding model: Bedrock Titan v2 (text-embed) — consistent, low-latency.

LLMs: Bedrock Claude 3.5 Sonnet (alignment/rationales), OpenAI GPT-4.1-mini (lightweight JSON-mode tasks).

Schedulers/Jobs: Railway cron for nightly rebuilds (graph refresh, trust rescoring, risk recompute).

Search: Vector search in Postgres (pgvector) for simplicity; Pinecone optional later.

Secrets: Vercel env for frontend, Railway env for backend (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET, BEDROCK_REGION, OPENAI_API_KEY).

File processing: Lambda-style worker or Railway worker for heavy PDF chunking (avoid Vercel timeouts).

Observability: OpenTelemetry + JSON logs shipped to Logtail; per-module feature flags via env FEATURE_*.

Rollout order (with validation, logging, fallback)

EvidenceMapper™ (highest visible value)

Metric: Top-1 alignment precision on 20 hand-labeled artifacts ≥ 0.70; latency p95 < 8s.

Fallback: If vector/LLM fails, show “upload received, queued for indexing” + enqueue job.

Flag: FEATURE_EVIDENCE_MAPPER=true.

EvidenceTrust Score™

Metric: Inter-rater correlation with 2 SMEs ≥ 0.65; deterministic signals auditable.

Fallback: Display “insufficient metadata” with checklist.

Flag: FEATURE_EVIDENCE_TRUST=true.

CiteGuard™

Metric: Precision on synthetic test set ≥ 0.9 for “missing citation” detection.

Fallback: Soft warnings only.

Flag: FEATURE_CITEGUARD=true.

StandardsGraph™

Metric: 100% clause count parity with source; spot-check 30 edges for correctness.

Fallback: Serve prior snapshot.

Flag: FEATURE_STANDARDS_GRAPH=true.

GapRisk Predictor™

Metric: Backtest vs. SME-labeled risk tiers, MAE ≤ 0.12.

Fallback: Default to coverage-only risk.

Flag: FEATURE_GAP_RISK=true.

CrosswalkX™

Metric: SME acceptance rate of suggested pairs ≥ 70%.

Fallback: Only show pre-approved pairs.

Flag: FEATURE_CROSSWALK=true.

Safety nets (flags, rollbacks, test scaffolding)

Per-module flags listed above; all routes check flags and return 501 Not Enabled when off.

Rollback recipe: Toggle flag → revert env → redeploy; DB changes behind additive migrations only.

Golden tests: Cypress e2e (UI smoke), plus 10 JSON contract tests per endpoint with recorded fixtures.

Rate limits: /api/evidence/map 20/min per user; job queue backpressure.

PII/Confidentiality: All artifact text stays in DB/Storage; only embeddings leave process (never raw text); add “no external retention” header to LLM calls when provider supports it.

Sample payload pack (for Copilot to commit under /fixtures/)

fixtures/standards/SACSCOC_2024.json (nodes/clauses).

fixtures/artifacts/sample_policy.pdf + sample_policy.meta.json.

fixtures/align/request.json & fixtures/align/response.json.

fixtures/trust/request.json & fixtures/trust/response.json.

fixtures/crosswalk/response.json.

fixtures/risk/response.json.

fixtures/citations/response.json.

Action items Copilot can execute now

Migrations: add pgvector, create tables (artifacts, artifact_chunks, standards, clauses, standards_graph_edges, evidence_links, crosswalk_edges, trust_signals, citations).

Storage utils: S3 presign upload/download + MIME/virus scan stub (sync).

Chunker: PDF/DOCX → page chunks with offsets; store vectors.

Vector search: cosine similarity SQL helpers.

Endpoints: implement the six routes with the JSON contracts above.

Jobs: nightly cron for trust/risk/graph refresh.

Flags: env-driven feature toggles + middleware.

Tests: JSON contract tests + 3 Cypress flows (upload → map; view trust; run citeguard).