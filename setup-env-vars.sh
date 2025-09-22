#!/bin/bash

# Environment Variables Setup Helper Script
# This script helps you configure environment variables for Railway and Vercel

echo "🚀 MapMyStandards Environment Setup"
echo "===================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
if ! command_exists railway; then
    echo "❌ Railway CLI not found. Please install: npm install -g @railway/cli"
    exit 1
fi

if ! command_exists vercel; then
    echo "❌ Vercel CLI not found. Please install: npm install -g vercel"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Generate secure keys
generate_key() {
    if command_exists openssl; then
        openssl rand -hex 32
    else
        # Fallback to /dev/urandom
        head -c 32 /dev/urandom | base64 | tr -d "=+/" | cut -c1-32
    fi
}

# Railway Setup
echo "🚂 Railway Configuration"
echo "------------------------"

# Check if logged in
if railway whoami &>/dev/null; then
    echo "✅ Logged into Railway"
else
    echo "⚠️  Please login to Railway first: railway login"
    exit 1
fi

# Check if we need to generate keys
if [ ! -f railway.env ]; then
    echo "📝 Creating railway.env from template..."
    cp railway.env.template railway.env
    
    # Generate secure keys
    SECRET_KEY=$(generate_key)
    JWT_SECRET_KEY=$(generate_key)
    
    # Update the file with generated keys
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=/SECRET_KEY=$SECRET_KEY/" railway.env
        sed -i '' "s/JWT_SECRET_KEY=/JWT_SECRET_KEY=$JWT_SECRET_KEY/" railway.env
    else
        # Linux
        sed -i "s/SECRET_KEY=/SECRET_KEY=$SECRET_KEY/" railway.env
        sed -i "s/JWT_SECRET_KEY=/JWT_SECRET_KEY=$JWT_SECRET_KEY/" railway.env
    fi
    
    echo "✅ Generated secure keys for SECRET_KEY and JWT_SECRET_KEY"
    echo ""
    echo "⚠️  Please edit railway.env and add your API keys:"
    echo "   - STRIPE_SECRET_KEY"
    echo "   - STRIPE_WEBHOOK_SECRET" 
    echo "   - POSTMARK_SERVER_TOKEN"
    echo "   - OPENAI_API_KEY (optional)"
    echo "   - ANTHROPIC_API_KEY (optional)"
    echo ""
    echo "Press any key to continue after editing..."
    read -n 1 -s
fi

# Vercel Setup
echo ""
echo "▲ Vercel Configuration"
echo "----------------------"

# Check if logged in
if vercel whoami &>/dev/null; then
    echo "✅ Logged into Vercel"
else
    echo "⚠️  Please login to Vercel first: vercel login"
    exit 1
fi

# List key environment variables to check
echo ""
echo "📋 Required Vercel Environment Variables:"
echo "   - NEXT_PUBLIC_API_URL (should be: https://api.mapmystandards.ai)"
echo "   - NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY"
echo "   - VITE_API_URL (should be: https://api.mapmystandards.ai)"
echo "   - VITE_STRIPE_PUBLISHABLE_KEY"
echo ""

# Summary
echo "📊 Summary"
echo "----------"
echo ""
echo "1. Railway environment variables:"
echo "   - Template: railway.env.template"
echo "   - Config file: railway.env (edit this with your values)"
echo "   - Deploy: railway variables set < railway.env"
echo ""
echo "2. Vercel environment variables:"
echo "   - Template: vercel.env.template" 
echo "   - Add via: vercel env add [NAME] [VALUE] production"
echo "   - Or use Vercel Dashboard: https://vercel.com/dashboard"
echo ""
echo "3. Local development:"
echo "   - Create .env file from .env.example or use minimal values"
echo "   - Start server: python3 -m uvicorn src.a3e.main:app --reload"
echo ""
echo "📚 Full documentation: ENVIRONMENT_SETUP.md"
echo ""
echo "✅ Setup helper complete!"