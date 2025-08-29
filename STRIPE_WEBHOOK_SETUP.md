# Stripe Webhook Configuration Guide

## 📋 Steps to Configure Stripe Webhook

### 1. Access Stripe Dashboard
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Developers** → **Webhooks**
3. Click **"Add endpoint"**

### 2. Configure Webhook Endpoint
Enter these details:

- **Endpoint URL**: `https://api.mapmystandards.ai/api/stripe/webhook`
- **Description**: MapMyStandards Production Webhook
- **Events to listen for**: Select these events:
  - ✅ `checkout.session.completed`
  - ✅ `customer.subscription.created`
  - ✅ `customer.subscription.updated`
  - ✅ `customer.subscription.deleted`
  - ✅ `invoice.payment_succeeded`
  - ✅ `invoice.payment_failed`
  - ✅ `payment_intent.succeeded`
  - ✅ `payment_intent.payment_failed`

### 3. Get Webhook Secret
After creating the endpoint:
1. Click on the webhook you just created
2. Find **"Signing secret"** section
3. Click **"Reveal"** 
4. Copy the secret (starts with `whsec_`)

### 4. Add Secret to Railway
Run this command with your webhook secret:

```bash
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_YOUR_ACTUAL_SECRET_HERE"
```

Example:
```bash
railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_abcd1234567890..."
```

### 5. Verify Webhook Configuration
After setting the variable:

```bash
# Redeploy to apply the webhook secret
railway up

# Check if webhook secret is set
railway variables | grep STRIPE_WEBHOOK
```

### 6. Test Webhook
In Stripe Dashboard:
1. Go to your webhook endpoint
2. Click **"Send test webhook"**
3. Select event type: `checkout.session.completed`
4. Click **"Send test webhook"**
5. Check response should be 200 OK

## 🔍 Webhook URL Details

Your webhook endpoint is:
```
https://api.mapmystandards.ai/api/stripe/webhook
```

This endpoint will:
- Receive payment events from Stripe
- Update subscription status
- Send confirmation emails
- Update database records

## ⚠️ Important Notes

1. **Use Live Mode**: Make sure you're in Live mode (not Test mode) in Stripe Dashboard
2. **SSL Required**: The webhook URL must use HTTPS (already configured)
3. **Secret Required**: Without the webhook secret, events won't be processed
4. **Logs**: Monitor webhook events in Stripe Dashboard under Events

## 🧪 Testing the Webhook

### Using Stripe CLI (Optional)
```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to Stripe
stripe login

# Forward events to local endpoint (for testing)
stripe listen --forward-to https://api.mapmystandards.ai/api/stripe/webhook

# Trigger test event
stripe trigger checkout.session.completed
```

### Monitoring Webhook Events
1. **Stripe Dashboard**: Developers → Events
2. **Railway Logs**: `railway logs | grep stripe`
3. **API Logs**: Check for webhook processing messages

## ✅ Success Indicators

Your webhook is working when:
- Stripe Dashboard shows "200 OK" responses
- Payment events update database records
- Customers receive email confirmations
- Subscription statuses update correctly

## 🚨 Troubleshooting

### Common Issues:

**404 Not Found**
- Check endpoint URL is correct
- Ensure API is deployed and running

**401 Unauthorized**
- Webhook secret not set or incorrect
- Run: `railway variables --set "STRIPE_WEBHOOK_SECRET=whsec_..."`

**500 Internal Server Error**
- Check Railway logs: `railway logs`
- Database connection issues
- Missing environment variables

**No Response**
- API timeout
- Check Railway service health
- Verify custom domain is working