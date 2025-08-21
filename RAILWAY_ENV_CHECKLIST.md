# Railway Environment Variables Checklist

The following environment variables need to be set in Railway for the `prolific-fulfillment` project:

## Database
- [ ] `DATABASE_URL` - PostgreSQL connection string (Railway provides this)

## Stripe
- [ ] `STRIPE_SECRET_KEY` - Your Stripe secret key (starts with `sk_test_` or `sk_live_`)
- [ ] `STRIPE_WEBHOOK_SECRET` - Stripe webhook endpoint secret (starts with `whsec_`)
- [ ] `STRIPE_PRICE_ID_MONTHLY` - price_1Q0uElRx59MW7hVBHedTxnRw
- [ ] `STRIPE_PRICE_ID_ANNUAL` - price_1Q0uGXRx59MW7hVB8BUcNcrB
- [ ] `STRIPE_PRICE_ID_ONETIME` - price_1Q0uIKRx59MW7hVBEiUMXhka

## Email (Postmark)
- [ ] `POSTMARK_SERVER_TOKEN` - Your Postmark server API token
- [ ] `EMAIL_FROM` - noreply@mapmystandards.ai (or your sending email)

## Authentication
- [ ] `JWT_SECRET_KEY` - A secure random string for JWT tokens
- [ ] `SECRET_KEY` - A secure random string for sessions

## Application
- [ ] `ENVIRONMENT` - production
- [ ] `APP_URL` - https://platform.mapmystandards.ai
- [ ] `API_URL` - https://api.mapmystandards.ai

## To Add These Variables:

1. Go to Railway dashboard: https://railway.app
2. Navigate to the `prolific-fulfillment` project
3. Click on the `exemplary-solace` service
4. Go to the "Variables" tab
5. Add each variable with its value

## Generate Secure Keys:

For JWT_SECRET_KEY and SECRET_KEY, use:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Next Steps:

After adding all environment variables:
1. Railway will automatically redeploy
2. Test the API again with the test scripts
3. The 500 errors should be resolved
