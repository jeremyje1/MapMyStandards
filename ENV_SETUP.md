# Environment & Infrastructure Setup

This guide covers provisioning infrastructure (Railway + Vercel), managing secrets, and synchronizing local + production environment variables.

## 1. Prerequisites

- Node.js (LTS) & npm
- Railway CLI (`npm i -g @railway/cli`)
- Vercel CLI (`npm i -g vercel`) or use dashboard
- OpenSSL (for generating secure secrets)

## 2. Provision Production Postgres (Railway)

```bash
railway init --name mapmystandards-prod
railway add postgresql
# After creation:
railway variables
```

Copy the generated `DATABASE_URL` (or assemble from individual vars) and set it:

```bash
echo "DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DATABASE" >> .env.local
```

## 3. Create Local Env File

Use the provided template:

```bash
cp .env.production.template .env.local
```

Fill in all `__PLACEHOLDER__` values with development or staging equivalents. Keep production secrets ONLY in Vercel / Railway dashboards.

## 4. Generate Critical Secrets

```bash
openssl rand -base64 48 # for NEXTAUTH_SECRET
```

## 5. Stripe Setup

1. Create products + prices (Department, Campus, System, Pilot) in Stripe Dashboard (live mode).
2. Copy Price IDs to env keys:
   - `STRIPE_PRICE_DEPARTMENT_ANNUAL`
   - `STRIPE_PRICE_CAMPUS_ANNUAL`
   - `STRIPE_PRICE_SYSTEM_ANNUAL`
   - `STRIPE_PRICE_PILOT`
3. Create a webhook endpoint (e.g. `https://app.mapmystandards.ai/api/stripe/webhook`) and subscribe to:
   - `checkout.session.completed`
4. Copy the Webhook Signing Secret to `STRIPE_WEBHOOK_SECRET`.

## 6. Postmark Setup

1. Create Server → get Server Token → set `POSTMARK_API_TOKEN`.
2. Create (or confirm) Message Stream: `mapmystandards-transactional` → set `POSTMARK_MESSAGE_STREAM`.
3. Verify sending domain for `northpathstrategies.org` and confirm DKIM/SPF.

## 7. Object Storage (S3-Compatible)

Pick one provider (AWS S3, Cloudflare R2, Backblaze B2). Fill:
```
S3_ENDPOINT=...
S3_REGION=...
S3_BUCKET=...
S3_ACCESS_KEY=...
S3_SECRET_KEY=...
```
Future code will use these for artifact ingestion & evidence vault.

## 8. Vercel Environment Variables

In the Vercel project settings, add all keys from `.env.production.template` (omit comments). Use:
- Production environment: live secrets
- Preview/Development: staging/test values

Recommended grouping:
- Core URLs: `NEXT_PUBLIC_APP_URL`, `NEXTAUTH_URL`
- Auth: `NEXTAUTH_SECRET`
- Stripe: All `STRIPE_*`
- Email: `POSTMARK_*`, `FROM_EMAIL`, `REPLY_TO_EMAIL`
- Storage: `S3_*`
- Database: `DATABASE_URL`
- Misc: `DEV_ADMIN_TOKEN`

## 9. Local Development Flow

```bash
cp .env.production.template .env.local
# fill dev values
npm install
npm run dev
```

## 10. Security Notes

- Never commit populated `.env*` files.
- Rotate `NEXTAUTH_SECRET` if compromised (invalidate sessions).
- Restrict `STRIPE_SECRET_KEY` & DB access via least privilege.
- Separate staging vs production Stripe accounts where feasible.

## 11. Verification Checklist

| Area   | Check |
|--------|-------|
| Auth   | Magic link email sends (dev route or real flow) |
| Stripe | Checkout + webhook logs tier persistence stub |
| Email  | Postmark test email succeeds |
| DB     | (Future) Prisma migration runs |
| S3     | (Planned) Can put/get test object |

## 12. Next Steps

- Introduce Prisma schema & migrations for user + subscription tables.
- Implement persistent tier storage (replace `lib/db.ts`).
- Wire artifact storage service using S3 credentials.
- Add health/status endpoint aggregating Stripe, DB, Email checks.

---

Maintain parity between `.env.production.template` and any new variables introduced in code. Update this guide whenever a new integration lands.
