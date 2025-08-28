#!/bin/bash

# Setup Stripe Webhook for MapMyStandards A3E

echo "======================================"
echo "Stripe Webhook Setup Script"
echo "======================================"

# Check if stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo "❌ Stripe CLI is not installed. Please install it first."
    echo "   Visit: https://stripe.com/docs/stripe-cli"
    exit 1
fi

echo "✅ Stripe CLI is installed"
echo ""

# List existing webhooks
echo "Current webhook endpoints:"
stripe webhook_endpoints list --limit 5

echo ""
echo "======================================"
echo "Creating/Updating Webhook Endpoint"
echo "======================================"

# Production webhook URL
WEBHOOK_URL="https://api.mapmystandards.ai/api/v1/billing/webhook/stripe"

# Events to listen for
EVENTS="checkout.session.completed,customer.subscription.created,customer.subscription.updated,customer.subscription.deleted,invoice.payment_failed,invoice.payment_succeeded,payment_intent.succeeded"

echo "Webhook URL: $WEBHOOK_URL"
echo "Events: $EVENTS"
echo ""

# Create webhook endpoint
echo "Creating webhook endpoint..."
WEBHOOK_RESPONSE=$(stripe webhook_endpoints create \
  --url "$WEBHOOK_URL" \
  --enabled-events $EVENTS \
  --description "MapMyStandards A3E Production Webhook" 2>&1)

if [[ $WEBHOOK_RESPONSE == *"id"* ]]; then
    echo "✅ Webhook endpoint created successfully!"
    echo ""
    echo "Webhook details:"
    echo "$WEBHOOK_RESPONSE" | jq '{id, url, enabled_events, secret}'
    
    # Extract the webhook secret
    WEBHOOK_SECRET=$(echo "$WEBHOOK_RESPONSE" | jq -r '.secret')
    
    echo ""
    echo "======================================"
    echo "IMPORTANT: Save this webhook secret!"
    echo "======================================"
    echo "Add this to your .env file:"
    echo ""
    echo "STRIPE_WEBHOOK_SECRET=$WEBHOOK_SECRET"
    echo ""
    echo "This secret is used to verify that webhook requests are from Stripe."
else
    echo "⚠️  Webhook might already exist or there was an error:"
    echo "$WEBHOOK_RESPONSE"
    echo ""
    echo "To list existing webhooks:"
    echo "stripe webhook_endpoints list"
fi

echo ""
echo "======================================"
echo "Testing Webhook Locally (Optional)"
echo "======================================"
echo "To test webhooks locally during development, run:"
echo ""
echo "stripe listen --forward-to localhost:8000/api/v1/billing/webhook/stripe"
echo ""
echo "This will give you a temporary webhook secret for local testing."

echo ""
echo "======================================"
echo "Next Steps"
echo "======================================"
echo "1. Add the STRIPE_WEBHOOK_SECRET to your .env file"
echo "2. Deploy your application with the updated environment variables"
echo "3. Test the webhook by creating a test payment"
echo "4. Check Stripe Dashboard > Webhooks to see webhook logs"