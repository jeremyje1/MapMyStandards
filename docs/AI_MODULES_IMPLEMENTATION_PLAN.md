# AI Modules Implementation Plan

_Updated: 2025-10-10_

## Context Snapshot

- **Reference doc**: `web/MODULES_ALGORITHMS.md` defines desired behavior for StandardsGraph™, EvidenceMapper™, CrosswalkX™, GapRisk Predictor™, EvidenceTrust Score™, and CiteGuard™.
- **Drop-in starter pack**: includes a canonical Postgres schema (`database/schema.sql`), a production ready `.env.example`, and FastAPI route stubs under `src/a3e/api/` with TODO hooks for business logic.
- **Existing stack**: `src/a3e/` already ships a FastAPI app, SQLAlchemy session manager (`src/a3e/database/connection.py`), and legacy models. We will extend/replace portions to line up with the new schema while preserving feature-flag safety rails.

The goal is to wire real data flows (storage, embeddings, vector search, scoring, and jobs) behind the existing API scaffolding while keeping rollbacks simple.

## High-Level Phases

| Phase | Objective | Key Deliverables | Dependencies |
| --- | --- | --- | --- |
| 0 | Foundation inventory | Confirm env parity, catalog secrets, verify pgvector on Railway, align feature flags | Access to production `.env`, AWS + AI provider credentials |
| 1 | Database alignment | Alembic migration from `database/schema.sql`, SQLAlchemy models, DAL services, pgvector helper functions | Phase 0 |
| 2 | Storage & chunking | S3 client + presigned URL helpers, artifact ingestion pipeline, PDF/DOCX chunker with embeddings queue payload | Phase 1 |
| 3 | Embeddings & search | Bedrock/OpenAI client wrappers, embedding persistence to `artifact_chunks`, vector search SQL templates, ranking heuristics | Phase 2 |
| 4 | API feature logic | Implement TODOs for all six routers (EvidenceMapper, StandardsGraph, CrosswalkX, GapRisk, EvidenceTrust, CiteGuard) plus feature flag enforcement & error handling | Phases 1-3 |
| 5 | Jobs & schedulers | Railway cron worker for nightly recompute (risk, trust, standards refresh), retry/backoff strategy | Phases 1-4 |
| 6 | Testing & QA | Pytest fixtures mirroring JSON contracts, contract tests, smoke CLI, CI wiring; exploratory Cypress updates | Prior phases |
| 7 | Observability & rollout | Structured logging, OTEL hooks, metrics dashboards, launch playbook with rollback toggles | Parallel with Phases 4-6 |

## Detailed Task Breakdown

### Phase 0 — Foundation Inventory

1. **.env parity**
   - Diff existing `.env.example` vs starter pack; merge missing keys (AWS, Bedrock, OpenAI, feature flags, rate limits, OTEL).
   - Propagate to `RAILWAY_BACKEND.env` & Vercel (document owner).
2. **Secrets checklist** (needs confirmation from @jeremy):
   - `DATABASE_URL` (Railway) with vector-enabled Postgres.
   - AWS IAM user w/ S3 (bucket `mms-artifacts`) + Bedrock permission.
   - OpenAI API key with JSON mode access.
   - Optional Cohere credentials (future rerank).
3. **Infra validation**
   - Run `CREATE EXTENSION vector` on prod DB if not already.
   - Validate S3 bucket CORS + lifecycle.

### Phase 1 — Database Alignment

1. **Alembic migration**
   - Generate single migration script derived from `database/schema.sql` (idempotent `CREATE TABLE IF NOT EXISTS`, indexes, `pgvector`).
   - Tag migration version in `alembic.ini`.
2. **SQLAlchemy models** (new module `src/a3e/database/models.py`)
   - `Org`, `AppUser`, `Artifact`, `ArtifactChunk`, `Standard`, `StandardGraphEdge`, `EvidenceLink`, `CrosswalkEdge`, `TrustSignal`, `Citation`, `RiskSnapshot`.
   - Leverage SQLAlchemy `Vector` type (from `sqlalchemy_utils` or custom) mapped to pgvector.
3. **DAL services**
   - Reconcile with existing `DatabaseManager`; add repos/services for each table (CRUD, lookup by org/standard).
   - Implement vector operations via raw SQL where needed (embedding insert, cosine search).
4. **Data contracts**
   - Document shapes in Pydantic models to ensure parity with SQLAlchemy.

### Phase 2 — Storage & Chunking

1. **S3 utility module** (`src/a3e/services/storage.py`)
   - Presign upload/download, MIME detection, optional antivirus stub.
2. **Artifact ingestion pipeline**
   - Worker-friendly service to fetch artifact binary, page chunk (PDF via `pypdf`, DOCX via `python-docx`, HTML via `BeautifulSoup`).
   - Emit structured chunks (page, chunk_index, content, tokens) with metadata for embeddings queue.
3. **Queue orchestration**
   - Decide on immediate embed vs. asynchronous job; baseline plan uses synchronous embed for MVP with hooks for job queue (Redis / Railway cron).

### Phase 3 — Embeddings & Search Layer

1. **Client wrappers**
   - `src/a3e/services/embeddings.py`: unify Bedrock Titan + OpenAI fallback, caching, rate limit handling.
   - Use environment feature toggles for provider selection.
2. **Embedding persistence**
   - Insert chunk embeddings into `artifact_chunks` with VECTOR(1536) column.
   - Guarantee deterministic dimension; store provider metadata.
3. **Similarity search helpers**
   - SQL snippet: `SELECT artifact_id, page, chunk_index, 1 - (embedding <=> :query) AS score ...`.
   - Build Python helper returning top-K matches with threshold filters.
4. **LLM rerank** (optional but stubbed)
   - Use Claude 3.5 Sonnet to rerank top-K; store rationale strings.

### Phase 4 — API Logic by Module

1. **EvidenceMapper (`/api/evidence/map`)**
   - Validate artifact + org scope; ensure embeddings exist.
   - Run vector search, optional rerank, compute trust signals if `FEATURE_EVIDENCE_TRUST` on.
   - Upsert `evidence_links` rows; return matches sorted by score.
   - Fall back to background job if embeddings missing.
2. **EvidenceTrust (`/api/evidence/trust-score`)**
   - Derive deterministic signals (freshness, authenticity, redundancy, citation density) from metadata & `citations` table.
   - Persist in `trust_signals` and compute composite trust.
3. **StandardsGraph**
   - **POST /ingest**: fetch source (S3/local), parse to clause tree, upsert into `standards` + `standards_graph_edges`, queue background job when long-running; return queued status w/ job id.
   - **GET /graph**: query nodes & edges for `standard_set`, map to response schema.
4. **CrosswalkX**
   - **POST /build**: generate candidate pairs via text similarity (reuse embeddings) + heuristics; optionally call LLM refine; persist to `crosswalk_edges`.
   - **GET /**: read from `crosswalk_edges` and return `CrosswalkResponse`.
5. **GapRisk**
   - Combine standards coverage (from `evidence_links`), trust signals, crosswalk support; compute risk index; store snapshots.
   - Return most recent snapshot per org/standard_set.
6. **CiteGuard**
   - Extract citations from artifact (cached analysis); run GPT-4.1-mini JSON-mode; reconcile with regex checks; upsert into `citations`.
   - Response matches contract with issues list.

### Phase 5 — Jobs & Schedulers

- **Nightly cron worker** (`jobs/nightly_recompute.py`)
  - Refresh trust scores for aging artifacts.
  - Recompute risk snapshots.
  - Optionally refresh standards graph from source URLs.
- **Queue integration**
  - Simple Railway cron invocation for now; future upgrade path to Redis/Qdrant queue.
- **Monitoring**
  - Write job logs to structured logger; expose `/jobs/health` if needed.

### Phase 6 — Testing & QA

1. **Pytest fixtures** under `tests/fixtures/ai_contracts/`
   - JSON fixtures from starter pack (align, trust, crosswalk, risk, citations).
   - DB fixtures using transactional scope; embed synthetic vectors.
2. **Contract tests**
   - For each endpoint, test happy path + flag-disabled scenario + failure (missing artifact/standard).
3. **Integration smoke**
   - CLI script `scripts/ai_contract_smoke.py` to run end-to-end pipeline on sample artifact.
4. **Cypress updates**
   - Extend existing UI flows to cover EvidenceMapper results and CiteGuard warnings once backend stable.

### Phase 7 — Observability & Rollout

- **Logging**: ensure structured JSON logs (status, latency, provider usage) with PII scrubbing.
- **Metrics**: expose Prometheus-friendly counters (embedding calls, vector search latency, evidence matches per request).
- **Feature flags**: keep route-level flag checks; add per-provider toggles (e.g., `PROVIDER_BEDROCK_ENABLED`).
- **Rollout playbook**: update `DEPLOYMENT_CHECKLIST.md` with activation steps & rollback instructions.

## Immediate Next Actions

1. ✅ Merge `.env.example` additions and confirm required secrets availability (Railway env updated 2025-10-10).
2. ✅ Draft Alembic migration & SQLAlchemy models/DAL (Phase 1 foundations landed in this commit).
3. Prototype embedding service + artifact chunker using sample PDF to validate dimensions (Phase 2/3).
4. Stand up contract tests scaffold to guard responses before wiring heavy logic.

### Progress Log

- **2025-10-10**: Environment template aligned with AI module flags and provider secrets. Alembic migration `20251010_1500_add_ai_modules_schema` created for orgs/artifacts/standards graph/evidence/crosswalk/trust/citations/risk tables with pgvector support. New SQLAlchemy models (`src/a3e/database/ai_models.py`) and async repositories (`ai_repositories.py`) scaffolded for upcoming route integrations.
- **2025-10-10**: Prototype EvidenceMapper pipeline delivered. Added chunker + embedding services, route `/api/evidence/map`, and persistence back into `evidence_links`. New dependencies captured in `requirements.txt`.

## Risks & Open Questions

- **Secrets**: need confirmation on Bedrock access + S3 credentials; without them we can mock but not deploy.
- **pgvector version**: ensure Railway Postgres version supports `vector_cosine_ops` indexes; adjust list count if storage limited.
- **Worker capacity**: large PDFs may exceed FastAPI request budgets; might require asynchronous queue from day one.
- **Legacy data**: migrating from existing `accreditors`/`standards` tables must preserve current UX; plan for coexistence or migration script.

## Coordination Notes

- Coordinate with frontend team for any schema changes to API responses (should stay within documented contract).
- Document nightly job schedule & expected runtime for ops.
- Keep feature flags off in production until module-specific smoke tests pass.
- Provide progress updates in `docs/AI_MODULES_IMPLEMENTATION_PLAN.md` as phases complete.
