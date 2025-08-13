#!/usr/bin/env bash
set -euo pipefail

if ! command -v stripe >/dev/null 2>&1; then
  echo "Stripe CLI not installed. See: https://stripe.com/docs/stripe-cli" >&2
  exit 1
fi

PRICE_ID=${1:-${STRIPE_PRICE_DEPARTMENT_ANNUAL:-}}
if [ -z "$PRICE_ID" ]; then
  echo "Usage: $0 <price_id>  (or export STRIPE_PRICE_DEPARTMENT_ANNUAL)" >&2
  exit 1
fi

echo "Creating test Checkout Session for price $PRICE_ID ..."
stripe checkout sessions create \
  --mode=subscription \
  --customer-email "test-tier@example.com" \
  --line-items price=$PRICE_ID,quantity=1 \
  --success-url "http://localhost:3000/success?session_id={CHECKOUT_SESSION_ID}" \
  --cancel-url "http://localhost:3000/cancel"

echo "Now (optionally) trigger event replay: stripe trigger checkout.session.completed"
echo "Run: stripe listen --forward-to localhost:3000/api/stripe/webhook"
