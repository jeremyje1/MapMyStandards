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
echo "${STRIPE_API_KEY:?export STRIPE_API_KEY before running}" | vercel env add STRIPE_API_KEY development  # Set STRIPE_API_KEY env var before running

echo "📝 Adding STRIPE_WEBHOOK_SECRET..."
echo "${STRIPE_WEBHOOK_SECRET:?export STRIPE_WEBHOOK_SECRET before running}" | vercel env add STRIPE_WEBHOOK_SECRET development

echo "📝 Adding STRIPE_PUBLISHABLE_KEY..."
echo "${STRIPE_PUBLISHABLE_KEY:?export STRIPE_PUBLISHABLE_KEY before running}" | vercel env add STRIPE_PUBLISHABLE_KEY development

# Add application variables
echo "📝 Adding JWT_SECRET_KEY..."
echo "${JWT_SECRET_KEY:?export JWT_SECRET_KEY before running}" | vercel env add JWT_SECRET_KEY development

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
