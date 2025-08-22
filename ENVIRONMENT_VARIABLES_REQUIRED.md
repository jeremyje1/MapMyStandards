# Required Environment Variables for Production

## Critical - Trial Signup is Blocked Without These

The trial signup is currently failing because the production deployment is using **live Stripe keys** but the system is falling back to **test price IDs**. This creates a mismatch that Stripe rejects.

## Required Stripe Price Environment Variables

Set these in your deployment platform (e.g., AWS, Heroku, etc.):

```bash
# College Monthly Plan
STRIPE_PRICE_COLLEGE_MONTHLY=price_1RyVQ4K8PKpLCKDZON0IMe3F

# College Annual Plan  
STRIPE_PRICE_COLLEGE_ANNUAL=price_1RyVQJK8PKpLCKDZq7dKpXGt

# K12 Monthly Plan
STRIPE_PRICE_K12_MONTHLY=price_1RyVQhK8PKpLCKDZhcvczFv0

# K12 Annual Plan
STRIPE_PRICE_K12_ANNUAL=price_1RyVQwK8PKpLCKDZvjOxFuGb

# Personal Monthly Plan
STRIPE_PRICE_PERSONAL_MONTHLY=price_1RyVRBK8PKpLCKDZUH8Qh8Ko

# Personal Annual Plan
STRIPE_PRICE_PERSONAL_ANNUAL=price_1RyVRQK8PKpLCKDZbJqrfvnq
```

## How to Set These

### AWS (EC2/ECS/Lambda)
- For EC2: Add to `/etc/environment` or use systemd service files
- For ECS: Add to task definition environment variables
- For Lambda: Add in Lambda function configuration

### Heroku
```bash
heroku config:set STRIPE_PRICE_COLLEGE_MONTHLY=price_1RyVQ4K8PKpLCKDZON0IMe3F
heroku config:set STRIPE_PRICE_COLLEGE_ANNUAL=price_1RyVQJK8PKpLCKDZq7dKpXGt
# ... etc for all variables
```

### Docker
Add to your `docker-compose.production.yml` or pass via `-e` flags

### Verification

After setting these variables, verify they're working:

1. Visit: `https://yourdomain.com/trial/verify-prices`
2. Check that it shows the live price IDs, not test ones
3. Try a trial signup - it should work without 400 errors

## Current Protection

The code now includes a defensive check that will raise an error if:
- Live Stripe key is detected (starts with 'sk_live_')
- But environment variables are not set
- This prevents accidentally using test prices in production

## Important Notes

1. These are your **live** Stripe price IDs - handle them securely
2. Never commit these to version control
3. The system will refuse to use test prices with live keys as of the latest update
4. Without these variables, trial signups will fail with a clear error message

## Public URL Variables (New)

Set the public-facing base URLs used across emails, links, and tests:

```bash
PUBLIC_APP_URL=https://platform.mapmystandards.ai
PUBLIC_API_URL=https://api.mapmystandards.ai
```

These default to production domains if not set, but specifying them explicitly:
- Enables staging deployments (`https://staging.platform...`) without code edits
- Ensures emails and absolute links resolve correctly
- Keeps test code domain-agnostic

## URL Reference Best Practices

To avoid hard-coded domains scattered through the codebase:

1. Backend code: use `settings.PUBLIC_APP_URL` and `settings.PUBLIC_API_URL`.
2. Tests: import `API_BASE` / `APP_BASE` from `test_urls.py` (added in this repo).
3. Emails: rely on helper `build_unsubscribe_link()` and construct links via helpers.
4. Static HTML: prefer relative links (`/trial`, `/contact`) unless an absolute URL is required for external contexts.
5. Documentation: when referencing domains, prefer placeholders like `${PUBLIC_APP_URL}` where feasible.

Benefit: Single-point domain change (vars) instead of sweeping find/replace operations.

