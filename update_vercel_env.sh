#!/bin/bash

echo "🔄 Updating Vercel Environment Variables..."
echo "==========================================="

# Update existing incorrect price IDs
echo "📝 Updating STRIPE_MONTHLY_PRICE_ID..."
echo "price_1Rxb2wRMpSG47vNmCzxZGv5I" | vercel env add STRIPE_MONTHLY_PRICE_ID development --force

echo "📝 Updating STRIPE_ANNUAL_PRICE_ID..."
echo "price_1Rxb32RMpSG47vNmlMtDijH7" | vercel env add STRIPE_ANNUAL_PRICE_ID development --force

# Add missing Stripe variables
echo "📝 Adding STRIPE_ONETIME_PRICE_ID..."
echo "price_1Rxb3uRMpSG47vNmdMuVZlrn" | vercel env add STRIPE_ONETIME_PRICE_ID development

echo "📝 Adding STRIPE_API_KEY..."
echo "$STRIPE_API_KEY" | vercel env add STRIPE_API_KEY development  # Set STRIPE_API_KEY env var before running

echo "📝 Adding STRIPE_WEBHOOK_SECRET..."
echo "whsec_b4dc6a99fa351c7891f876b828f89f1f8a1fca947c1f4709a66b1a033228e72e" | vercel env add STRIPE_WEBHOOK_SECRET development

echo "📝 Adding STRIPE_PUBLISHABLE_KEY..."
echo "pk_test_51Rxag5RMpSG47vNmqhABDBgO7IJMlIgKxy07zsU9JiIespCNnQylscJZGYqMvoLA2mtLaNP8d6lkNSwePHrGefGw00JNrDhL0k" | vercel env add STRIPE_PUBLISHABLE_KEY development

# Add application variables
echo "📝 Adding JWT_SECRET_KEY..."
echo "7UKtJWo1jG6Yji-Fw-0t1HRC6y8QsPojrWkEJhEXXTQV0myYJIJ183xEPLcT6vDcPjLR_mB9tBQsGejvTxg-QA" | vercel env add JWT_SECRET_KEY development

echo "📝 Adding DATABASE_URL..."
echo "sqlite:///data/a3e_dev.db" | vercel env add DATABASE_URL development

echo "📝 Adding API_BASE_URL..."
echo "https://api.mapmystandards.ai" | vercel env add API_BASE_URL development

echo ""
echo "✅ Environment variables update complete!"
echo ""
echo "📋 Verifying updated variables..."
vercel env pull .env.vercel.updated

echo ""
echo "🔍 Check .env.vercel.updated to verify all variables are correct"
