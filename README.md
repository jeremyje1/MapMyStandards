# A³E — Autonomous Accreditation & Audit Engine

A3E ingests institutional artefacts (LMS exports, SharePoint docs, SIS data), drops them in a vector store, and orchestrates an LLM‑agent swarm to generate:

* a Standards × Evidence matrix  
* draft narrative text per criterion  
* a traffic‑light gap dashboard  

The stack is polyglot‑friendly but defaults to **Python 3.12**, **Postgres + Milvus**, and AWS Bedrock LLM endpoints.

> **Live demo** – coming soon at https://api.YOURDOMAIN.ai/docs
# Trigger deployment
# Force redeploy to MapMyStandards service
# Force redeploy Fri Aug 29 18:04:39 CDT 2025


## Frontend Deployment (Vercel)

- Preferred deploy: from the repository root (not from `/web`).
- The root `vercel.json` controls redirects, headers, and API rewrites, and its `outputDirectory` points to `web`.

Commands

```bash
# From repo root
vercel deploy --prod --yes

# Verify health (or run the VS Code task "Check prod deployment")
./check_deployment.sh
```

Common pitfalls

- Do not deploy from `/web`. If `/web/.vercel/` exists, remove it to avoid linking the subfolder to a different project:

```bash
rm -rf web/.vercel
```

- Confirm the linked project at root:

```bash
cat .vercel/project.json
```

Troubleshooting

- If `platform.mapmystandards.ai` doesn’t update after a deploy, confirm you deployed from the root and that the domain is attached to the root project. The response headers at `https://platform.mapmystandards.ai/reports-modern` should reflect the latest `Last-Modified` and contain the new UI elements (e.g., the “Upload now” CTA).
