# MapMyStandards Two-Domain Architecture

## 🌐 Domain Structure

### 1. Main Marketing Site: `mapmystandards.ai`
**Purpose:** WordPress-powered marketing homepage only
**File:** `wordpress_marketing_homepage.html`
**Content:**
- Hero section with value proposition
- Simple CTA directing to platform
- Minimal content, maximum impact
- All links direct to `platform.mapmystandards.ai`

### 2. Platform Site: `platform.mapmystandards.ai`
**Purpose:** Complete SaaS application and functionality
**Deployment:** Vercel + Railway
**Key Files:**
- `platform_homepage.html` (main entry point)
- `trial.html` (trial request form)
- `pricing.html` (pricing with Stripe integration)
- `login.html` (authentication)
- `dashboard.html` (post-payment welcome)
- Backend API files

## 🚀 User Journey

### New Prospects:
1. **Discover** → `mapmystandards.ai` (WordPress marketing)
2. **Interested** → Click CTA → `platform.mapmystandards.ai`
3. **Explore** → Platform homepage with options
4. **Trial** → `platform.mapmystandards.ai/trial.html`
5. **Purchase** → `platform.mapmystandards.ai/pricing.html` → Stripe
6. **Onboard** → `platform.mapmystandards.ai/dashboard.html`
7. **Use** → `platform.mapmystandards.ai/login.html`

### Existing Users:
1. **Access** → Direct to `platform.mapmystandards.ai/login.html`
2. **Dashboard** → Full platform functionality

## 💳 Payment & Stripe Integration

### Secure Environment Variables:
- `STRIPE_SECRET_KEY` - Your live Stripe secret key
- `STRIPE_MONTHLY_PRICE_ID` - Monthly plan price ID
- `STRIPE_YEARLY_PRICE_ID` - Annual plan price ID

### Pricing:
- **Monthly:** $49.99/month
- **Annual:** $499/year (17% discount)
- **Trial:** 7 days free, no credit card required

### Stripe Checkout Flow:
1. User clicks pricing plan
2. Redirects to Stripe checkout
3. After payment → `platform.mapmystandards.ai/dashboard.html`
4. Dashboard guides to login for platform access

## 🔧 Technical Setup

### Files Created/Updated:
1. **wordpress_marketing_homepage.html** - WordPress marketing site
2. **platform_homepage.html** - Platform main page
3. **trial.html** - Trial request form
4. **pricing.html** - Pricing with Stripe integration
5. **create_stripe_products_secure.py** - Secure Stripe product setup
6. **create_payment_links_secure.py** - Secure payment link creation
7. **vercel.json** - Updated deployment configuration

### Environment Variables Needed:
```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_...
STRIPE_MONTHLY_PRICE_ID=price_...
STRIPE_YEARLY_PRICE_ID=price_...

# Optional: Generated checkout URLs
STRIPE_MONTHLY_CHECKOUT_URL=https://buy.stripe.com/...
STRIPE_YEARLY_CHECKOUT_URL=https://buy.stripe.com/...
```

## 📋 Deployment Checklist

### 1. WordPress Site (`mapmystandards.ai`):
- [ ] Upload `wordpress_marketing_homepage.html` content to WordPress
- [ ] Update homepage template
- [ ] Test all links point to platform domain

### 2. Platform Site (`platform.mapmystandards.ai`):
- [ ] Deploy to Vercel with custom domain
- [ ] Set environment variables in Vercel dashboard
- [ ] Test all pages load correctly
- [ ] Verify Stripe integration works

### 3. Stripe Setup:
- [ ] Run `python create_stripe_products_secure.py` to create products
- [ ] Run `python create_payment_links_secure.py` to create checkout links
- [ ] Update environment variables with generated IDs
- [ ] Test checkout flow end-to-end

### 4. DNS Configuration:
- [ ] Point `platform.mapmystandards.ai` to Vercel
- [ ] Verify SSL certificates
- [ ] Test domain resolution

## 🎯 Key Benefits

1. **Clean Separation:** Marketing vs. functionality
2. **SEO Optimized:** WordPress for marketing content
3. **Scalable Platform:** Modern SaaS architecture
4. **Secure Payments:** Environment-based Stripe integration
5. **Professional UX:** Clear user journey and conversion flow

## 📈 Next Steps

1. Deploy and test the architecture
2. Set up analytics tracking
3. Configure email notifications for trials
4. Add more platform features (analytics, reports, etc.)
5. Implement user authentication and data storage

## 🔒 Security Notes

- All Stripe keys use environment variables
- No sensitive data in code repository
- FERPA-compliant data handling
- Secure payment processing through Stripe

---

This architecture provides a clean separation between marketing and platform functionality, ensuring optimal user experience and conversion rates while maintaining security and scalability.

## Additional Platform Scaffolding (2025-08 Iteration)

New components added in feature branch `feat/mms-vault-mapping-dashboard`:

- Vault Mapping Dashboard scaffold (`/app/vault-mapping/page.tsx`) – placeholder UI showing planned KPIs & heat map area.
- Tier feature definitions (`lib/tiers.ts`) and tier persistence stub (`lib/tierPersistence.ts`).
- In-memory DB abstraction (`lib/db.ts`) to unblock early persistence flows prior to Prisma/SQL integration.
- Stripe webhook now resolves tier from price IDs and calls tier persistence stub.
- Postmark email abstraction (`lib/email/postmark.ts`).
- Vitest testing harness (`vitest.config.ts`) with initial tests in `tests/` for tiers and in-memory DB.

### Testing

Run unit tests:

```
npm install
npm test
```

Planned future work: replace `lib/db.ts` with real ORM layer, expand test coverage to API routes (Stripe checkout, webhook, support contact), and integrate end-to-end mapping tests once data models are finalized.
