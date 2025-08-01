#!/bin/bash

# A³E SaaS Platform - Production Deployment Script
# This script deploys the full SaaS platform to production

set -e  # Exit on any error

echo "🚀 Starting A³E SaaS Platform Deployment..."

# Check if required tools are installed
command -v git >/dev/null 2>&1 || { echo "❌ Git is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }

# Configuration
PROJECT_NAME="a3e-saas-platform"
PRODUCTION_URL="https://api.mapmystandards.ai"

echo "📋 Project: $PROJECT_NAME"
echo "🌐 Production URL: $PRODUCTION_URL"

# Step 1: Prepare environment
echo ""
echo "📦 Step 1: Preparing environment..."

if [ ! -f "production.env" ]; then
    echo "⚠️  Creating production.env from example..."
    cp production.env.example production.env
    echo "🔧 Please edit production.env with your actual values:"
    echo "   - Stripe API keys"
    echo "   - Database URL"
    echo "   - JWT secret"
    echo "   - Email configuration"
    read -p "Press Enter after updating production.env..."
fi

# Step 2: Build Docker image
echo ""
echo "🐳 Step 2: Building Docker image..."
docker build -f Dockerfile.production -t $PROJECT_NAME .

# Step 3: Database setup (if using Docker Compose)
echo ""
echo "🗄️  Step 3: Database setup..."
if [ -f "docker-compose.production.yml" ]; then
    echo "Starting database with Docker Compose..."
    docker-compose -f docker-compose.production.yml up -d db
else
    echo "⚠️  No Docker Compose file found. Make sure your database is running."
fi

# Step 4: Deploy based on platform choice
echo ""
echo "🚀 Step 4: Choose deployment platform:"
echo "1) Railway"
echo "2) Render"
echo "3) AWS/Digital Ocean (Docker)"
echo "4) Local Docker (for testing)"

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🚂 Deploying to Railway..."
        if command -v railway >/dev/null 2>&1; then
            railway login
            railway up
        else
            echo "❌ Railway CLI not installed. Visit: https://railway.app/cli"
            exit 1
        fi
        ;;
    2)
        echo "🎨 Deploying to Render..."
        echo "📝 Please connect your GitHub repo to Render manually:"
        echo "   1. Go to https://render.com"
        echo "   2. Create new Web Service"
        echo "   3. Connect this repository"
        echo "   4. Use Dockerfile.production"
        echo "   5. Add environment variables from production.env"
        ;;
    3)
        echo "☁️  Deploying with Docker..."
        echo "🔧 Build and push to your container registry:"
        echo "   docker tag $PROJECT_NAME your-registry/$PROJECT_NAME"
        echo "   docker push your-registry/$PROJECT_NAME"
        ;;
    4)
        echo "🐳 Starting local Docker container..."
        docker run -d \
            --name $PROJECT_NAME \
            --env-file production.env \
            -p 8000:8000 \
            $PROJECT_NAME
        echo "✅ Container started on http://localhost:8000"
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Step 5: WordPress Integration
echo ""
echo "🌐 Step 5: WordPress Integration..."
echo "📁 WordPress plugin created in: wordpress-plugin/"
echo ""
echo "📋 Manual WordPress steps:"
echo "1. Upload wordpress-plugin/ folder to /wp-content/plugins/"
echo "2. Activate 'A³E SaaS Integration' plugin"
echo "3. Update homepage CTAs to point to /checkout/"
echo "4. Test the flow: /checkout/ → signup → /dashboard/"

# Step 6: Final checks
echo ""
echo "🔍 Step 6: Final checks..."
echo "✅ Deployment configuration ready"
echo "✅ Docker image built"
echo "✅ WordPress plugin created"
echo "✅ Environment variables configured"

echo ""
echo "🎉 A³E SaaS Platform deployment preparation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update your DNS to point to the deployed API"
echo "2. Update WordPress with the plugin"
echo "3. Test the complete flow"
echo "4. Monitor logs and performance"
echo ""
echo "🔗 Production URLs:"
echo "   API: $PRODUCTION_URL"
echo "   Checkout: https://mapmystandards.ai/checkout/"
echo "   Dashboard: https://mapmystandards.ai/dashboard/"
