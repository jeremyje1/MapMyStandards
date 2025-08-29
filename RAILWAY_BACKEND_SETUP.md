# Railway Backend Setup Instructions

## Current Status
✅ Successfully linked to backend project: **prolific-fulfillment**
⚠️ Service selection needed (multiple services in project)

## Next Steps

### 1. Select the Backend Service Interactively
Run this command in your terminal (not through Claude):
```bash
railway service
```
Then select the backend service from the list.

### 2. Once Service is Selected, Update Variables

You can either:

#### Option A: Use Railway Dashboard (Easiest)
1. Go to https://railway.app/project/1a6b310c-fa1b-43ee-96bc-e093cf175829
2. Click on the backend service
3. Go to "Variables" tab
4. Click "Raw Editor"
5. Paste the complete ENV variables from RAILWAY_BACKEND.env

#### Option B: Use Railway CLI Commands
After selecting the service, run these commands:

```bash
# Update all Stripe Price IDs
railway variables --set STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY=price_1S1PIaK8PKpLCKDZxRRzTP59
railway variables --set STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL=price_1S1PIkK8PKpLCKDZqxmtxUeG
railway variables --set STRIPE_PRICE_ID_INSTITUTION_MONTHLY=price_1RyVQgK8PKpLCKDZTais3Tyx
railway variables --set STRIPE_PRICE_ID_INSTITUTION_ANNUAL=price_1RyVQrK8PKpLCKDZUshqaOvZ
railway variables --set STRIPE_PRICE_ID_STARTER_MONTHLY=price_1RyVPPK8PKpLCKDZFbwkFdqq
railway variables --set STRIPE_PRICE_ID_STARTER_ANNUAL=price_1RyVPgK8PKpLCKDZe8nu4ium

# Update legacy variables
railway variables --set STRIPE_PRICE_COLLEGE_MONTHLY=price_1S1PIaK8PKpLCKDZxRRzTP59
railway variables --set STRIPE_PRICE_COLLEGE_YEARLY=price_1S1PIkK8PKpLCKDZqxmtxUeG
railway variables --set STRIPE_PRICE_MULTI_CAMPUS_MONTHLY=price_1RyVQgK8PKpLCKDZTais3Tyx
railway variables --set STRIPE_PRICE_MULTI_CAMPUS_YEARLY=price_1RyVQrK8PKpLCKDZUshqaOvZ

# Update CORS origins
railway variables --set "CORS_ORIGINS=https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://*.railway.app"

# Update URLs
railway variables --set FRONTEND_URL=https://platform.mapmystandards.ai
railway variables --set BACKEND_URL=https://api.mapmystandards.ai
```

### 3. Deploy the Backend
```bash
railway up --detach
```

## Project Information
- **Project ID**: 1a6b310c-fa1b-43ee-96bc-e093cf175829
- **Project Name**: prolific-fulfillment
- **Environment**: production
- **Domain**: api.mapmystandards.ai