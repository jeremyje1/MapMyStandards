# Stripe Pricing Configuration - IMPORTANT

## Current Setup (As of January 2025)

### ✅ ACTIVE CONFIGURATION
- **Single Pricing Tier**: $199/month
- **Price ID**: `price_1S2yYNK8PKpLCKDZ6zgFu2ay`
- **Mode**: Monthly subscription only
- **Location**: Hardcoded in `/app/api/stripe/checkout/route.ts`

### 📍 Key Files
1. **Checkout Route** (MAIN FILE - DO NOT CHANGE)
   - Path: `/app/api/stripe/checkout/route.ts`
   - Contains hardcoded price ID
   - Creates Stripe checkout session for $199/month subscription

2. **Environment Files** (FOR REFERENCE ONLY - NOT USED)
   - `.env` files contain legacy price IDs but are NOT used
   - The checkout route does NOT read from environment variables
   - Price ID is HARDCODED in the route file

### ⚠️ IMPORTANT NOTES
- **DO NOT** modify the checkout route to add multiple tiers
- **DO NOT** add complex pricing logic
- **DO NOT** rely on environment variables for price IDs
- The system uses a SINGLE $199/month price tier ONLY

### 🚫 Files to IGNORE
These files contain OLD/LEGACY pricing configurations:
- `/lib/tiers.ts` - Old multi-tier system (department/campus/system)
- `/test_new_pricing.py` - Old testing script
- `.env.pricing` - Old pricing environment variables
- `.env.stripe` - Old Stripe configuration
- Any file referencing:
  - STRIPE_PRICE_DEPARTMENT_*
  - STRIPE_PRICE_CAMPUS_*
  - STRIPE_PRICE_SYSTEM_*
  - STRIPE_PRICE_PILOT
  - Multiple pricing tiers

### ✅ How Checkout Works
1. User clicks checkout button
2. Frontend calls `/api/stripe/checkout` (POST request)
3. Backend creates Stripe session with hardcoded `price_1S2yYNK8PKpLCKDZ6zgFu2ay`
4. User redirected to Stripe hosted checkout
5. Payment processed for $199/month subscription

### 🔧 If You Need to Change the Price
1. Get new price ID from Stripe Dashboard
2. Update ONLY this line in `/app/api/stripe/checkout/route.ts`:
   ```typescript
   const MONTHLY_PRICE_ID = 'price_1S2yYNK8PKpLCKDZ6zgFu2ay';
   ```
3. Commit and deploy to Railway

### 📝 Deployment Notes
- **Backend (Railway)**: Handles checkout session creation
- **Frontend (Vercel)**: Displays UI, calls backend API
- Auto-deploys from main branch pushes

### 🎯 Quick Commands
```bash
# View current checkout implementation
cat app/api/stripe/checkout/route.ts

# Test checkout locally
curl -X POST http://localhost:3000/api/stripe/checkout

# Deploy changes
git add app/api/stripe/checkout/route.ts
git commit -m "Update Stripe checkout"
git push origin main
```

---
**Last Updated**: January 2025
**Verified Working**: Yes
**DO NOT MODIFY WITHOUT REVIEWING THIS DOCUMENT**