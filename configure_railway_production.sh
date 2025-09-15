#!/bin/bash

echo "🚀 Configuring Railway Production Environment"
echo "==========================================="

# Set the database URL (Railway should auto-inject this, but we can verify)
echo "📝 Setting environment variables..."

# Set webhook secret
railway variables --set STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:?export STRIPE_WEBHOOK_SECRET before running}

# Verify DATABASE_URL is set correctly
echo ""
echo "✅ Verifying environment variables:"
railway variables | grep -E "(DATABASE_URL|STRIPE_WEBHOOK_SECRET)"

echo ""
echo "🔄 Redeploying to apply changes..."
railway up

echo ""
echo "✅ Configuration complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test a new signup at https://platform.mapmystandards.ai/subscribe"
echo "2. Check logs: railway logs --tail 50"
echo "3. Look for webhook and provisioning messages"
