#!/bin/bash

# Script to update backend environment variables for MapMyStandards
# Run this after linking to the prolific-fulfillment project

echo "🔧 Updating Backend Environment Variables for MapMyStandards..."
echo ""
echo "Current project status:"
railway status
echo ""
echo "⚠️  Note: You need to manually select the service in Railway dashboard"
echo "   or use 'railway service' command interactively"
echo ""
echo "Once service is linked, run the following commands to set variables:"
echo ""
cat << 'EOF'
# Stripe Configuration - MapMyStandards Account (LIVE)
railway variables --set STRIPE_PUBLISHABLE_KEY=pk_live_51Rr4dNK8PKpLCKDZH9u9mOEqmPVSR946uGYKSdk73mmNjBR4i9Ibon3wvDLNpYPRzsXmaAXTrwSPKKxNolArj8G200tZyrr6qE

# Stripe Price IDs - Professional Tier ($299/mo, $2,999/yr)
railway variables --set STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY=price_1S1PIaK8PKpLCKDZxRRzTP59
railway variables --set STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL=price_1S1PIkK8PKpLCKDZqxmtxUeG

# Stripe Price IDs - Institution Tier ($599/mo, $5,999/yr)
railway variables --set STRIPE_PRICE_ID_INSTITUTION_MONTHLY=price_1RyVQgK8PKpLCKDZTais3Tyx
railway variables --set STRIPE_PRICE_ID_INSTITUTION_ANNUAL=price_1RyVQrK8PKpLCKDZUshqaOvZ

# Stripe Price IDs - Starter Tier ($99/mo, $999/yr)
railway variables --set STRIPE_PRICE_ID_STARTER_MONTHLY=price_1RyVPPK8PKpLCKDZFbwkFdqq
railway variables --set STRIPE_PRICE_ID_STARTER_ANNUAL=price_1RyVPgK8PKpLCKDZe8nu4ium

# Legacy Stripe Price Variables (for backward compatibility)
railway variables --set STRIPE_PRICE_COLLEGE_MONTHLY=price_1S1PIaK8PKpLCKDZxRRzTP59
railway variables --set STRIPE_PRICE_COLLEGE_YEARLY=price_1S1PIkK8PKpLCKDZqxmtxUeG
railway variables --set STRIPE_PRICE_MULTI_CAMPUS_MONTHLY=price_1RyVQgK8PKpLCKDZTais3Tyx
railway variables --set STRIPE_PRICE_MULTI_CAMPUS_YEARLY=price_1RyVQrK8PKpLCKDZUshqaOvZ

# CORS Configuration
railway variables --set "CORS_ORIGINS=https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://*.railway.app"

# Application URLs
railway variables --set FRONTEND_URL=https://platform.mapmystandards.ai
railway variables --set BACKEND_URL=https://api.mapmystandards.ai
railway variables --set PUBLIC_URL=https://api.mapmystandards.ai

# Environment Settings
railway variables --set ENVIRONMENT=production
railway variables --set DEBUG=False
railway variables --set LOG_LEVEL=INFO
EOF

echo ""
echo "📝 Or use the Railway dashboard to paste the ENV format variables"