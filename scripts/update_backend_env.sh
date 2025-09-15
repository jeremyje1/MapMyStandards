#!/bin/bash

# Script to update backend environment variables for MapMyStandards
# Run this in the backend Railway project

echo "🔧 Updating Backend Environment Variables for MapMyStandards..."

# Update Stripe Price IDs to MapMyStandards account (LIVE mode)
# Professional tier - $299/month, $2,999/year
railway variables --set STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY=price_1S1PIaK8PKpLCKDZxRRzTP59
railway variables --set STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL=price_1S1PIkK8PKpLCKDZqxmtxUeG

# Institution tier - $599/month, $5,999/year  
railway variables --set STRIPE_PRICE_ID_INSTITUTION_MONTHLY=price_1RyVQgK8PKpLCKDZTais3Tyx
railway variables --set STRIPE_PRICE_ID_INSTITUTION_ANNUAL=price_1RyVQrK8PKpLCKDZUshqaOvZ

# Starter tier - $99/month, $999/year
railway variables --set STRIPE_PRICE_ID_STARTER_MONTHLY=price_1RyVPPK8PKpLCKDZFbwkFdqq
railway variables --set STRIPE_PRICE_ID_STARTER_ANNUAL=price_1RyVPgK8PKpLCKDZe8nu4ium

# Update legacy price variable names for backward compatibility
railway variables --set STRIPE_PRICE_COLLEGE_MONTHLY=price_1S1PIaK8PKpLCKDZxRRzTP59
railway variables --set STRIPE_PRICE_COLLEGE_YEARLY=price_1S1PIkK8PKpLCKDZqxmtxUeG
railway variables --set STRIPE_PRICE_MULTI_CAMPUS_MONTHLY=price_1RyVQgK8PKpLCKDZTais3Tyx
railway variables --set STRIPE_PRICE_MULTI_CAMPUS_YEARLY=price_1RyVQrK8PKpLCKDZUshqaOvZ

# Update Stripe Publishable Key to MapMyStandards account (LIVE mode)
railway variables --set STRIPE_PUBLISHABLE_KEY=pk_live_51Rr4dNK8PKpLCKDZH9u9mOEqmPVSR946uGYKSdk73mmNjBR4i9Ibon3wvDLNpYPRzsXmaAXTrwSPKKxNolArj8G200tZyrr6qE

# Ensure webhook endpoint secret is set (if not already present)
# export STRIPE_WEBHOOK_SECRET=whsec_...   # set before running

# Update CORS origins to include all production domains
railway variables --set "CORS_ORIGINS=https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://*.railway.app,https://mapmystandards-prod-production.up.railway.app"

echo "✅ Environment variables updated!"
echo ""
echo "📝 Summary of changes:"
echo "  - Updated all Stripe price IDs to MapMyStandards account (LIVE mode)"
echo "  - Updated Stripe publishable key to MapMyStandards account"
echo "  - Added platform.mapmystandards.ai to CORS origins"
echo "  - Configured legacy price variables for backward compatibility"
echo ""
echo "⚠️  Important: Make sure the STRIPE_SECRET_KEY is also set to the LIVE key"
echo "    It should start with: sk_live_51Rr4dNK8PKpLCKDZ..."
echo ""
echo "🚀 Now redeploy the backend service to apply changes:"
echo "  railway redeploy --yes"