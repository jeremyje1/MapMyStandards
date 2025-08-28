#!/bin/bash

# Deploy to Railway Script for MapMyStandards A3E

echo "======================================"
echo "Railway Deployment Script"
echo "======================================"

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed."
    echo "   Install it with: npm install -g @railway/cli"
    echo "   Or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

echo "✅ Railway CLI is installed"
echo ""

# Check if logged in to Railway
echo "Checking Railway authentication..."
railway whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Not logged in to Railway. Logging in..."
    railway login
fi

echo "✅ Authenticated with Railway"
echo ""

# Set environment variables
echo "======================================"
echo "Setting Environment Variables"
echo "======================================"

# Read from .env file and set in Railway
if [ -f .env ]; then
    echo "Found .env file. Setting production environment variables..."
    
    # Critical variables to set (with live values)
    railway variables set \
        STRIPE_SECRET_KEY="sk_live_YOUR_ACTUAL_LIVE_KEY_HERE" \
        STRIPE_PUBLISHABLE_KEY="pk_live_51Rxag5RMpSG47vNmE0GkLZ6xVBlXC2D8TS5FUSDI4VoKc5mJOzZu8JOKzmMMYMLtAONF7wJUfz6Wi4jKpbS2rBEi00tkzmeJgx" \
        STRIPE_PRICE_COLLEGE_MONTHLY="price_1RyVEORMpSG47vNmYL4DWCYF" \
        STRIPE_PRICE_COLLEGE_YEARLY="price_1RyVEWRMpSG47vNmiQjLhvqt" \
        STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY="price_1RyVEORMpSG47vNmYL4DWCYF" \
        STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL="price_1RyVEWRMpSG47vNmiQjLhvqt" \
        STRIPE_PRICE_MULTI_CAMPUS_MONTHLY="price_1RyVElRMpSG47vNmWNWcxCEB" \
        STRIPE_PRICE_MULTI_CAMPUS_YEARLY="price_1RyVEtRMpSG47vNmyZDQcjUm" \
        STRIPE_PRICE_ID_INSTITUTION_MONTHLY="price_1RyVElRMpSG47vNmWNWcxCEB" \
        STRIPE_PRICE_ID_INSTITUTION_ANNUAL="price_1RyVEtRMpSG47vNmyZDQcjUm" \
        DATABASE_URL="$DATABASE_URL" \
        JWT_SECRET_KEY="$(openssl rand -base64 32)" \
        SECRET_KEY="$(openssl rand -base64 32)" \
        PUBLIC_APP_URL="https://platform.mapmystandards.ai" \
        RAILWAY_ENVIRONMENT="production"
    
    echo "✅ Environment variables set"
else
    echo "⚠️  No .env file found. Please create one first."
    echo "   Copy .env.example to .env and fill in your values."
fi

echo ""
echo "======================================"
echo "Pre-deployment Checklist"
echo "======================================"

# Check for critical files
echo "Checking critical files..."
FILES_TO_CHECK=(
    "Dockerfile"
    "railway.json"
    "requirements.txt"
    "src/a3e/main.py"
    "web/trial-signup.html"
    "web/checkout.html"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file exists"
    else
        echo "  ❌ $file not found"
    fi
done

echo ""
echo "======================================"
echo "⚠️  IMPORTANT: Live Mode Configuration"
echo "======================================"
echo "You need to:"
echo "1. Get your live secret key from Stripe Dashboard"
echo "2. Replace 'sk_live_YOUR_ACTUAL_LIVE_KEY_HERE' in this script"
echo "3. Or manually set it in Railway dashboard after deployment"
echo ""
echo "Current mode: LIVE (real charges will occur!)"
echo ""

# Confirm deployment
read -p "Do you want to continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

echo ""
echo "======================================"
echo "Deploying to Railway"
echo "======================================"

# Deploy
railway up

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✅ Deployment Successful!"
    echo "======================================"
    
    # Get deployment URL
    echo "Getting deployment URL..."
    railway domain
    
    echo ""
    echo "Next steps:"
    echo "1. Add your live Stripe secret key in Railway dashboard"
    echo "2. Configure Stripe webhooks for production URL"
    echo "3. Test the checkout flow at /trial-signup.html"
    echo "4. Monitor logs with: railway logs"
    
    echo ""
    echo "Useful commands:"
    echo "  railway logs          - View application logs"
    echo "  railway status        - Check deployment status"
    echo "  railway variables     - List environment variables"
    echo "  railway domain        - Get deployment URL"
    echo "  railway open          - Open Railway dashboard"
else
    echo ""
    echo "❌ Deployment failed. Check the error messages above."
    echo "   Run 'railway logs' to see detailed error logs."
    exit 1
fi