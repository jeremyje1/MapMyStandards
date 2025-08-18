#!/bin/bash

# A³E Engine Deployment Script
# Quick deployment to Railway or other hosting platform

echo "🚀 A³E Engine Deployment Script"
echo "================================"

# Check if files exist
if [ ! -f "a3e_main_deploy.py" ]; then
    echo "❌ Error: a3e_main_deploy.py not found"
    exit 1
fi

if [ ! -f "requirements-a3e-deploy.txt" ]; then
    echo "❌ Error: requirements-a3e-deploy.txt not found"
    exit 1
fi

echo "✅ Deployment files ready"

# Option 1: Railway Deployment
echo ""
echo "📦 Railway Deployment Option:"
echo "1. railway login"
echo "2. railway init (create new project: mapmystandards-a3e)"
echo "3. Copy these files to deployment folder:"
echo "   - a3e_main_deploy.py"
echo "   - requirements-a3e-deploy.txt"
echo "4. railway up"
echo "5. railway domain (set to engine.mapmystandards.ai)"

# Option 2: Manual Testing
echo ""
echo "🧪 Local Testing:"
echo "python a3e_main_deploy.py"
echo "Then visit: http://localhost:8000"

# Option 3: Docker
echo ""
echo "🐳 Docker Deployment:"
echo "docker build -f Dockerfile.a3e -t a3e-engine ."
echo "docker run -p 8000:8000 a3e-engine"

echo ""
echo "🎯 Target URL: https://engine.mapmystandards.ai"
echo "📚 API Docs: https://engine.mapmystandards.ai/docs"
echo "🔍 Health: https://engine.mapmystandards.ai/health"

echo ""
echo "🎉 Ready for deployment!"
