# MapMyStandards Single Plan Environment Setup

## Current Status (Phase E Complete)

### ✅ Implemented Features:
1. **Onboarding** - Available at `/onboarding.html` with API support
2. **Evidence Upload** - API endpoints at `/api/v1/upload/*`
3. **Stripe Integration** - Webhook handler exists, needs single plan price ID
4. **Authentication** - JWT-based auth with `has_active_subscription` check

### ❌ Missing Features (Need Implementation):
1. **Org Chart** - No implementation found
2. **Scenario/ROI Modeling** - Backend calculations exist, no UI
3. **Power BI Dashboard** - No embed configuration
4. **Enterprise Dashboard Route** - Not implemented

## Required Environment Variables

### Vercel (Frontend)
```bash
# Add to Vercel dashboard
NEXT_PUBLIC_API_URL=https://api.mapmystandards.ai
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...

# Single plan Stripe configuration
NEXT_PUBLIC_STRIPE_SINGLE_PLAN_PRICE_ID=price_SINGLE_199_MONTHLY
```

### Railway (Backend)
```bash
# Core
SECRET_KEY=[generate]
DATABASE_URL=postgresql://...
FRONTEND_URL=https://platform.mapmystandards.ai

# Stripe Single Plan
STRIPE_SECRET_KEY=sk_live_...
STRIPE_SINGLE_PLAN_PRICE_ID=price_SINGLE_199_MONTHLY
STRIPE_WEBHOOK_SECRET=whsec_...

# Power BI (when implemented)
POWERBI_CLIENT_ID=
POWERBI_CLIENT_SECRET=
POWERBI_TENANT_ID=
POWERBI_WORKSPACE_ID=
POWERBI_REPORT_ID=
```

## Navigation Updates Needed

Update `/web/dashboard.html` or create a new dashboard with links to:
- `/onboarding.html` - ✅ Already exists
- `/org-chart.html` - ❌ Need to create
- `/scenario-modeling.html` - ❌ Need to create  
- `/enterprise-dashboard.html` - ❌ Need to create
- `/upload.html` - ✅ Already exists

## Single Plan Implementation

All features are now accessible with `has_active_subscription` check:
- No more tier restrictions
- $199/month gives access to everything
- Trial users also get full access during trial period

## Next Steps

1. Create missing UI pages for org chart, scenario modeling
2. Add Power BI environment variables
3. Update dashboard navigation menu
4. Test single plan checkout flow with new price ID
