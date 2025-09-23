#!/bin/bash

# Deployment script to fix all critical issues
# Run with: ./deploy_fixes.sh

echo "🚀 MapMyStandards Deployment Fixes"
echo "=================================="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command_exists git; then
    echo "❌ Git not installed"
    exit 1
fi

if ! command_exists vercel; then
    echo "❌ Vercel CLI not installed"
    echo "Install with: npm install -g vercel"
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# 1. Update login page
echo "📄 Updating login page..."
if [ -f "web/login-enhanced-v2.html" ]; then
    echo "✅ Enhanced login page exists"
else
    echo "❌ Enhanced login page not found"
fi

# 2. Deploy frontend to Vercel
echo ""
echo "🌐 Deploying frontend to Vercel..."
echo "This will fix 404 errors on navigation links"
read -p "Deploy to Vercel production? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd web
    vercel --prod
    cd ..
    echo "✅ Frontend deployed"
else
    echo "⏭️  Skipped frontend deployment"
fi

# 3. Check backend status
echo ""
echo "🔧 Checking backend status..."
response=$(curl -s -o /dev/null -w "%{http_code}" https://api.mapmystandards.ai/api/health)
if [ "$response" == "404" ] || [ "$response" == "200" ]; then
    echo "✅ Backend API is reachable (status: $response)"
else
    echo "❌ Backend API unreachable or error (status: $response)"
fi

# 4. Test authentication endpoint
echo ""
echo "🔐 Testing authentication..."
auth_response=$(curl -s -w "\n%{http_code}" -X POST https://api.mapmystandards.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"Test123!@#"}' | tail -n 1)

if [ "$auth_response" == "500" ]; then
    echo "❌ Authentication endpoint returning 500 error"
    echo ""
    echo "To fix this, you need to:"
    echo "1. Check Railway logs: railway logs -n 100"
    echo "2. Update the auth endpoint code"
    echo "3. Redeploy: git push"
elif [ "$auth_response" == "200" ]; then
    echo "✅ Authentication working!"
else
    echo "⚠️  Authentication returned unexpected status: $auth_response"
fi

# 5. Summary
echo ""
echo "📊 Deployment Summary"
echo "===================="
echo ""

# Count working pages
working_pages=0
total_pages=9

for page in dashboard-enhanced.html standards-graph-enhanced.html compliance-dashboard-enhanced.html \
           reports-enhanced.html organizational-enhanced.html settings-enhanced.html \
           about-enhanced.html contact-enhanced.html onboarding.html; do
    if [ -f "web/$page" ]; then
        ((working_pages++))
    fi
done

echo "📄 Pages created: $working_pages/$total_pages"
echo "🔐 Auth status: $([[ "$auth_response" == "200" ]] && echo "✅ Working" || echo "❌ Broken")"
echo "🌐 Frontend deployed: $([[ $REPLY =~ ^[Yy]$ ]] && echo "✅ Yes" || echo "❌ No")"

# 6. Next steps
echo ""
echo "📝 Next Steps:"
echo "============="
if [ "$auth_response" != "200" ]; then
    echo "1. Fix authentication error (CRITICAL)"
    echo "   - Check Railway logs"
    echo "   - Update src/a3e/api/routes/auth.py"
    echo "   - Deploy: git add . && git commit -m 'Fix auth' && git push"
fi

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "2. Deploy frontend pages"
    echo "   - Run: cd web && vercel --prod"
fi

echo "3. Test the complete user flow"
echo "   - Run: python3 test_complete_user_flow.py"
echo ""
echo "4. Implement UX improvements"
echo "   - Loading states"
echo "   - Error handling"
echo "   - Mobile menu"

echo ""
echo "✨ Deployment check complete!"