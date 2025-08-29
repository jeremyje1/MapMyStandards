#!/bin/bash

# Deploy frontend to Railway
echo "🚀 Deploying frontend to Railway..."

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Not in frontend directory"
    exit 1
fi

# Build the application
echo "📦 Building React application..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✅ Build successful!"

# Deploy to Railway
echo "🚂 Deploying to Railway..."
railway up --detach

echo "✅ Deployment initiated!"
echo "📊 Check deployment status at: https://railway.app/dashboard"