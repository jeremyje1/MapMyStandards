#!/bin/bash
# Deploy document fixes to Railway

echo "🚀 Deploying document management fixes..."

# Add and commit the changes
git add src/a3e/api/routes/user_intelligence_simple.py
git add web/upload-working.html

git commit -m "Fix document management: Add delete endpoint, fix API_BASE, correct download URLs"

# Push to trigger Railway deployment
git push origin main

echo "✅ Fixes deployed! Railway will automatically redeploy the backend."
echo ""
echo "📋 Changes deployed:"
echo "- Fixed API_BASE undefined error in upload page"
echo "- Added DELETE /documents/{id} endpoint for document deletion"
echo "- Fixed download URLs to use correct /uploads/{id} endpoint"
echo ""
echo "🔍 Monitor deployment at: https://railway.app/project/[your-project-id]"