#!/bin/bash
# Deploy API endpoint fixes to Railway and Vercel

echo "🚀 Deploying API endpoint fixes..."

# Add and commit the changes
git add src/a3e/api/routes/user_intelligence_simple.py
git add web/dashboard-modern.html
git add web/upload-working.html

git commit -m "Fix API endpoints: Add dashboard endpoints, fix API URLs in frontend"

# Push to trigger Railway deployment
git push origin main

echo "✅ Backend fixes deployed to Railway!"
echo ""
echo "📋 Changes deployed:"
echo "- Added /documents/list endpoint"
echo "- Added /documents/recent endpoint"
echo "- Added /compliance/summary endpoint"
echo "- Added /risk/summary endpoint"
echo "- Fixed dashboard API URLs to use api.mapmystandards.ai"
echo "- Fixed undefined dashboard variable error"
echo ""

# Deploy frontend to Vercel
echo "🚀 Deploying frontend to Vercel..."
cd web && vercel --prod

echo ""
echo "✅ All fixes deployed!"
echo ""
echo "🔍 Test the fixes:"
echo "1. Upload page: https://platform.mapmystandards.ai/upload-working.html"
echo "2. Dashboard: https://platform.mapmystandards.ai/dashboard-modern.html"
echo "3. Check browser console for any remaining errors"