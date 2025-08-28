# 🔴 LIVE Mode Stripe Setup

## Current Configuration

You have **TWO checkout systems** available:

### 1. ✅ **RECOMMENDED: `/trial-signup.html`**
- **Robust multi-step checkout** with professional UI
- Collects payment info properly via Stripe Elements
- Creates user account with password
- Better conversion rates with progress indicators
- **API Endpoint**: `/api/trial/signup`

### 2. ⚠️ **Basic: `/checkout.html`** 
- Simple single-page form (now fixed with payment collection)
- Less polished but functional
- **API Endpoint**: `/api/v1/billing/trial/signup`

## Live Mode Configuration Status

### ✅ Configured:
- **Live Publishable Key**: `pk_live_51Rxag5RMpSG47vNmE0GkLZ6x...` 
- **Price IDs**: All correctly mapped to your live Stripe products
- **Checkout pages**: Both pages updated with Stripe Elements

### ⚠️ Action Required:
You need to add your **Live Secret Key** to `.env`:

1. **Get your live secret key**:
   - Go to: https://dashboard.stripe.com/apikeys
   - Copy the live secret key (starts with `sk_live_`)
   
2. **Update `.env` file**:
   ```bash
   # Replace this line in .env:
   STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY_HERE
   
   # With your actual key:
   STRIPE_SECRET_KEY=sk_live_51Rxag5RMpSG47vNm[rest_of_your_key]
   ```

## Testing Live Mode

### ⚠️ WARNING: Live mode uses REAL money!

To test the checkout flow:

1. **Use the recommended checkout page**:
   ```
   https://yourdomain.com/trial-signup.html?plan=college_monthly
   ```

2. **Available plans**:
   - `college_monthly` - $297/month
   - `college_yearly` - $2,970/year (save $588)
   - `multicampus_monthly` - $897/month
   - `multicampus_yearly` - $8,073/year (save $1,691)

3. **Monitor in Stripe Dashboard**:
   - Go to: https://dashboard.stripe.com/payments
   - Watch for new customers and subscriptions
   - Check the Events log for webhook activity

## Quick Test Checklist

- [ ] Add live secret key to `.env`
- [ ] Restart your application to load new environment variables
- [ ] Navigate to `/trial-signup.html?plan=college_monthly`
- [ ] Complete the multi-step form
- [ ] Use a real credit card (or virtual card from Privacy.com)
- [ ] Verify customer created in Stripe Dashboard
- [ ] Verify subscription created with 7-day trial
- [ ] Check API key is returned and stored

## Recommended Deployment Steps

### 1. **Set Environment Variables on Production**:

For Railway:
```bash
railway variables set STRIPE_SECRET_KEY=sk_live_your_actual_key
railway variables set STRIPE_PUBLISHABLE_KEY=pk_live_51Rxag5RMpSG47vNmE0GkLZ6x...
railway variables set STRIPE_PRICE_COLLEGE_MONTHLY=price_1RyVEORMpSG47vNmYL4DWCYF
railway variables set STRIPE_PRICE_COLLEGE_YEARLY=price_1RyVEWRMpSG47vNmiQjLhvqt
railway variables set STRIPE_PRICE_MULTI_CAMPUS_MONTHLY=price_1RyVElRMpSG47vNmWNWcxCEB
railway variables set STRIPE_PRICE_MULTI_CAMPUS_YEARLY=price_1RyVEtRMpSG47vNmyZDQcjUm
```

### 2. **Configure Webhooks**:

Run the webhook setup script:
```bash
./setup_stripe_webhook.sh
```

Or manually in Stripe Dashboard:
- Go to: https://dashboard.stripe.com/webhooks
- Add endpoint: `https://api.mapmystandards.ai/api/v1/billing/webhook/stripe`
- Select events: 
  - `checkout.session.completed`
  - `customer.subscription.created`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`

### 3. **Update Marketing Links**:

Replace all checkout links to use the robust system:
```html
<!-- Old -->
<a href="/checkout.html?plan=college_monthly">Start Free Trial</a>

<!-- New (Recommended) -->
<a href="/trial-signup.html?plan=college_monthly">Start Free Trial</a>
```

## Price Reference

| Plan | Monthly | Yearly | Savings |
|------|---------|--------|---------|
| **College/Professional** | $297 | $2,970 | $588/year |
| **Multi-Campus/Institution** | $897 | $8,073 | $1,691/year |

## Monitoring & Support

### Check System Status:
```bash
# Verify configuration
python3 test_stripe_config.py

# Check API endpoints
curl https://api.mapmystandards.ai/api/v1/billing/config/debug | python3 -m json.tool
curl https://api.mapmystandards.ai/api/v1/billing/trial/diagnose | python3 -m json.tool
```

### Stripe Dashboard Links:
- **Payments**: https://dashboard.stripe.com/payments
- **Customers**: https://dashboard.stripe.com/customers
- **Subscriptions**: https://dashboard.stripe.com/subscriptions
- **Events Log**: https://dashboard.stripe.com/events
- **Webhook Logs**: https://dashboard.stripe.com/webhooks

## Safety Tips

1. **Use virtual cards** from Privacy.com for testing
2. **Set up alerts** in Stripe for new payments
3. **Monitor closely** for the first few real transactions
4. **Have refund process** ready if needed
5. **Keep test mode keys** commented in `.env` for easy switching

## Ready to Go Live?

Once you've added your live secret key to `.env`, your checkout system will be fully operational in LIVE mode. The robust `/trial-signup.html` page is recommended for the best user experience and conversion rates.