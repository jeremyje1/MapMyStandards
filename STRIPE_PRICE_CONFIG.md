# Stripe Price Configuration

## Production Price ID
The MapMyStandards platform uses a single subscription plan:
- **Price ID**: `price_1S2yYNK8PKpLCKDZ6zgFu2ay`
- **Amount**: $199/month
- **Description**: Full platform access with all features

## Environment Variable Configuration

### Option 1: Using Railway CLI
```bash
railway variables --set STRIPE_SINGLE_PLAN_PRICE_ID=price_1S2yYNK8PKpLCKDZ6zgFu2ay
```

### Option 2: Using Railway Dashboard
1. Go to your Railway project
2. Navigate to Variables tab
3. Add: `STRIPE_SINGLE_PLAN_PRICE_ID` = `price_1S2yYNK8PKpLCKDZ6zgFu2ay`

### Alternative Environment Variable Names
The system will check for the price ID in this order:
1. `STRIPE_SINGLE_PLAN_PRICE_ID`
2. `STRIPE_PRICE_MONTHLY` 
3. `STRIPE_MONTHLY_PRICE_ID`
4. `STRIPE_PRICE_COLLEGE_MONTHLY`
5. `STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY`

If none are set, it will use the hardcoded production price ID.

## Verification
After deployment, verify the configuration:
1. Visit: `https://api.mapmystandards.ai/api/v1/billing/single-plan-info`
2. Check that `stripe_price_id` shows the correct price ID
3. Test checkout at: `/web/subscribe.html`
