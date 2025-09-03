#!/bin/bash

echo "🚀 Deploying MapMyStandards to Railway..."

# Check if we're in the right directory
if [ ! -f "subscription_backend.py" ]; then
    echo "❌ subscription_backend.py not found. Make sure you're in the right directory."
    exit 1
fi

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not installed. Install it first:"
    echo "npm install -g @railway/cli"
    exit 1
fi

# Login to Railway (if not already logged in)
echo "📡 Logging into Railway..."
railway login

# Initialize project if needed
if [ ! -f "railway.toml" ]; then
    echo "🔧 Initializing Railway project..."
    railway init
fi

# Deploy the application
echo "🚀 Deploying application..."
railway up

# Check deployment status
echo "✅ Checking deployment status..."
railway status

echo ""
echo "🎉 Deployment complete!"
echo "Run 'railway open' to view your deployed application"
echo "Run 'railway logs' to view application logs"
echo ""
echo "📋 Next steps:"
echo "1. Get your Railway URL from the dashboard"
echo "2. Configure Stripe webhook with: YOUR_RAILWAY_URL/webhook"
echo "3. Test the health check: YOUR_RAILWAY_URL/health"
echo "4. Test the signup flow"
