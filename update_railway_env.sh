#!/bin/bash

echo "🚂 Updating Railway Environment Variables..."
echo "==========================================="

# Email Configuration
echo "📧 Adding email configuration..."
railway variables \
  --set "ADMIN_EMAIL=${ADMIN_EMAIL:-info@northpathstrategies.org}" \
  --set "FROM_EMAIL=${FROM_EMAIL:-info@northpathstrategies.org}" \
  --set "REPLY_TO_EMAIL=${REPLY_TO_EMAIL:-info@northpathstrategies.org}" \
  --set "MAILER_SEND_API_KEY=${MAILER_SEND_API_KEY:?export MAILER_SEND_API_KEY before running}" \
  --set "POSTMARK_API_TOKEN=${POSTMARK_API_TOKEN:?export POSTMARK_API_TOKEN before running}" \
  --set "POSTMARK_MESSAGE_STREAM=${POSTMARK_MESSAGE_STREAM:-mapmystandards-transactional}" \
  --skip-deploys

# Stripe Configuration
echo "💳 Adding Stripe configuration..."
railway variables \
  --set "STRIPE_MONTHLY_PRICE_ID=price_1Rxb2wRMpSG47vNmCzxZGv5I" \
  --set "STRIPE_ANNUAL_PRICE_ID=price_1Rxb32RMpSG47vNmlMtDijH7" \
  --set "STRIPE_ONETIME_PRICE_ID=price_1Rxb3uRMpSG47vNmdMuVZlrn" \
  --set "STRIPE_API_KEY=${STRIPE_API_KEY:?export STRIPE_API_KEY before running}" \
  --set "STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:?export STRIPE_WEBHOOK_SECRET before running}" \
  --set "STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY:?export STRIPE_PUBLISHABLE_KEY before running}" \
  --skip-deploys

# Application Configuration
echo "🔧 Adding application configuration..."
railway variables \
  --set "NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL:-https://app.mapmystandards.ai}" \
  --set "JWT_SECRET_KEY=${JWT_SECRET_KEY:?export JWT_SECRET_KEY before running}" \
  --set "API_BASE_URL=${API_BASE_URL:-https://api.mapmystandards.ai}" \
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
