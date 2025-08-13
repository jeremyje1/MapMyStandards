# Copilot Agent Playbook — MAPMYSTANDARDS

## Mission
Stand up accreditation evidence mapping SaaS using the same stack/patterns as Realign:
- Stripe tiers + webhook assignment + onboarding email.
- Uploads `/api/upload` for evidence/artifacts:contentReference[oaicite:51]{index=51}.
- AI narrative PDF generation `/api/report/generate` for self‑study sections:contentReference[oaicite:52]{index=52}.
- Tier‑gated advanced features (scenarios optional; Power BI optional later).

## Domain & env (suggested)
NEXT_PUBLIC_DOMAIN=app.mapmystandards.ai
NEXT_PUBLIC_APP_URL=https://app.mapmystandards.ai
# ... (same env keys as Realign; omit Power BI if you’re not ready)

**ASK THE USER (exact prompts):**
1) “Confirm MapMyStandards domain: app.mapmystandards.ai (Y/n).”
2) “Paste values for NEXTAUTH_SECRET, OPENAI_API_KEY, STRIPE keys. Choose email provider.”

## Steps
- Repeat Steps B–E from Realign (Railway DB, Vercel, Stripe products/prices/webhook).
- Reuse email wiring (welcome + onboarding → `/assessment/onboarding`):contentReference[oaicite:53]{index=53}.
- Enable uploads `/api/upload` for CSV/XLSX/PDF/DOCX/ZIP:contentReference[oaicite:54]{index=54}.
- Reuse AI PDF endpoint for standard‑aligned narratives:contentReference[oaicite:55]{index=55}.
- If you include scenario/ROI later, reuse engine endpoints/patterns:contentReference[oaicite:56]{index=56}.

## Smoke tests
- `/assessment/onboarding` renders, tier‑aware:contentReference[oaicite:57]{index=57}.
- `/api/upload` accepts CSV/XLSX/PDF (evidence):contentReference[oaicite:58]{index=58}.
- `/api/report/generate` returns a PDF:contentReference[oaicite:59]{index=59}.
- Stripe checkout + webhook assigns tier; gated routes work (if any).

## Pricing Tiers (Annual)
| Tier | Env Price Var | Annual USD | Key Caps |
|------|---------------|------------|----------|
| Department | STRIPE_PRICE_DEPARTMENT_ANNUAL | 9000 | 1 set / 500 artifacts / 5 users / 4 AI narratives |
| Campus | STRIPE_PRICE_CAMPUS_ANNUAL | 24000 | 3 sets / 3000 artifacts / 15 users / unlimited narratives |
| System | STRIPE_PRICE_SYSTEM_ANNUAL | 48000 | 10 sets / unlimited artifacts / 40 users / unlimited narratives / SSO / API |
| Enterprise | (custom) | 75000+ | Unlimited / SSO / API / premium support |
| Pilot (90 Day) | STRIPE_PRICE_PILOT | 4995 (one-time) | 1 set / 250 artifacts / 3 users / 1 narrative |

Set Stripe Price IDs in env; webhook maps price->tier dynamically.
