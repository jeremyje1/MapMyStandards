#!/bin/bash

echo "🚂 Updating Railway Environment Variables..."
echo "==========================================="

# Email Configuration
echo "📧 Adding email configuration..."
railway variables \
  --set "ADMIN_EMAIL=info@northpathstrategies.org" \
  --set "FROM_EMAIL=info@northpathstrategies.org" \
  --set "REPLY_TO_EMAIL=info@northpathstrategies.org" \
  --set "MAILER_SEND_API_KEY=[REDACTED_FOR_SECURITY]" \
  --set "POSTMARK_API_TOKEN=[REDACTED_FOR_SECURITY]" \
  --set "POSTMARK_MESSAGE_STREAM=mapmystandards-transactional" \
  --skip-deploys

# Stripe Configuration
echo "💳 Adding Stripe configuration..."
railway variables \
  --set "STRIPE_MONTHLY_PRICE_ID=price_1Rxb2wRMpSG47vNmCzxZGv5I" \
  --set "STRIPE_ANNUAL_PRICE_ID=price_1Rxb32RMpSG47vNmlMtDijH7" \
  --set "STRIPE_ONETIME_PRICE_ID=price_1Rxb3uRMpSG47vNmdMuVZlrn" \
  --set "STRIPE_API_KEY=sk_test_YOUR_STRIPE_TEST_KEY_HERE" \
  --set "STRIPE_WEBHOOK_SECRET=whsec_b4dc6a99fa351c7891f876b828f89f1f8a1fca947c1f4709a66b1a033228e72e" \
  --set "STRIPE_PUBLISHABLE_KEY=pk_test_51Rxag5RMpSG47vNmqhABDBgO7IJMlIgKxy07zsU9JiIespCNnQylscJZGYqMvoLA2mtLaNP8d6lkNSwePHrGefGw00JNrDhL0k" \
  --skip-deploys

# Application Configuration
echo "🔧 Adding application configuration..."
railway variables \
  --set "NEXT_PUBLIC_APP_URL=https://app.mapmystandards.ai" \
  --set "JWT_SECRET_KEY=7UKtJWo1jG6Yji-Fw-0t1HRC6y8QsPojrWkEJhEXXTQV0myYJIJ183xEPLcT6vDcPjLR_mB9tBQsGejvTxg-QA" \
  --set "API_BASE_URL=https://api.mapmystandards.ai" \
  --skip-deploys

# Database Configuration - Using Railway's PostgreSQL
echo "🗄️ Adding database configuration..."
echo "⚠️  Note: DATABASE_URL should be set to Railway's PostgreSQL instance"
echo "    Railway usually provides this automatically when you provision a PostgreSQL database"

echo ""
echo "✅ Environment variables update complete!"
echo ""
echo "📋 Verifying variables..."
railway variables
