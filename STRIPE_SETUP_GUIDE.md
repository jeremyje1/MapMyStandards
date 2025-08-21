# Stripe Setup Guide for MapMyStandards A³E Platform

## The Issue
The error "Invalid API Key provided: pk_test_*****" occurs because:
1. The Stripe environment variables are not set in Railway
2. The trial-signup.html page was using a hardcoded placeholder key

## What Was Fixed
1. Added `/api/v1/billing/config/stripe-key` endpoint to serve the Stripe publishable key dynamically
2. Updated trial-signup.html to fetch the key from the API instead of using hardcoded value
3. Added proper error handling and initialization checks

## Required Railway Environment Variables

You need to add these 3 environment variables in Railway:

### 1. STRIPE_SECRET_KEY
- **Required**: YES
- **Format**: `sk_test_...` (test mode) or `sk_live_...` (production)
- **Purpose**: Server-side API key for creating charges, customers, etc.

### 2. STRIPE_PUBLISHABLE_KEY  
- **Required**: YES
- **Format**: `pk_test_...` (test mode) or `pk_live_...` (production)
- **Purpose**: Client-side key for Stripe.js and payment forms

### 3. STRIPE_WEBHOOK_SECRET
- **Required**: Optional (but recommended)
- **Format**: `whsec_...`
- **Purpose**: Verifies webhook payloads from Stripe

## How to Set Up in Railway

1. **Get Your Stripe Keys**:
   - Log in to [Stripe Dashboard](https://dashboard.stripe.com)
   - Go to **Developers** → **API keys**
   - Copy your test or live keys

2. **Add to Railway**:
   - Go to your Railway project
   - Click on your service (platform.mapmystandards.ai)
   - Go to **Variables** tab
   - Click **+ New Variable**
   - Add each variable:
     ```
     STRIPE_SECRET_KEY = sk_test_YOUR_KEY_HERE
     STRIPE_PUBLISHABLE_KEY = pk_test_YOUR_KEY_HERE
     STRIPE_WEBHOOK_SECRET = whsec_YOUR_SECRET_HERE
     ```
   - Railway will automatically redeploy

3. **Verify Setup**:
   - After deployment, visit: https://platform.mapmystandards.ai/api/v1/billing/config/stripe-key
   - You should see:
     ```json
     {
       "publishable_key": "pk_test_...",
       "environment": "test"
     }
     ```

## Test vs Live Mode

- **Test Mode** (recommended for now):
  - Keys start with `sk_test_` and `pk_test_`
  - Use test card numbers like `4242 4242 4242 4242`
  - No real charges are made

- **Live Mode** (when ready for production):
  - Keys start with `sk_live_` and `pk_live_`
  - Real charges will be processed
  - Requires activated Stripe account

## Troubleshooting

1. **Still getting "Invalid API Key" error?**
   - Check Railway logs for deployment status
   - Ensure variables are saved in Railway
   - Try redeploying manually

2. **Payment form not loading?**
   - Check browser console for errors
   - Verify the /config/stripe-key endpoint is accessible
   - Ensure Stripe.js is loaded on the page

3. **Test the configuration**:
   ```bash
   curl https://platform.mapmystandards.ai/api/v1/billing/config/stripe-key
   ```

## Next Steps

After setting up the environment variables:
1. The trial signup form should work properly
2. Test with Stripe test cards
3. Monitor Railway logs for any errors
4. When ready, switch to live keys for production

## Support

If you need help:
- Check Railway deployment logs
- Run the diagnostic script: `python check_stripe_config.py`
- Contact support with error details
