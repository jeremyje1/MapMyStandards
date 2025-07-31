# 01 – High‑level architecture

```mermaid
graph TD
  A[Connectors] --> B[ETL]
  B --> C[Vector DB (Milvus)]
  C --> D[Agent Orchestra (AutoGen)]
  D --> E[REST & GraphQL API]
  E --> F[Web Dashboard] & G[VS Code Extension]
  D --> H[PDF Builder]
```

**Connectors**: Airbyte sources (Canvas, Banner, SharePoint, G‑Drive).

**Vector store**: Milvus on AWS EKS, hybrid search (BM25 + emb).

**Agent roles**

* **Mapper** – classifies artefacts → standards.
* **GapFinder** – marks missing evidence.
* **Narrator** – drafts prose paragraphs.
* **Verifier** – checks citations (≥ 0.85 cosine).

**CI/CD**: GitHub Actions → AWS ECR → ECS Fargate (scale‑to‑zero).

**Security**: all LLM calls in‑VPC via Bedrock with no retention; PII masked.
