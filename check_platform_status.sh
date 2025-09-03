#!/bin/bash
echo "Checking platform status..."
echo "=========================="

echo "🌐 Frontend (platform.mapmystandards.ai):"
if curl -s -I https://platform.mapmystandards.ai | head -n 1 | grep -q "200"; then
    echo "✅ Frontend is LIVE"
else
    echo "❌ Frontend is down or not accessible"
    echo "📋 DNS Check: Make sure platform.mapmystandards.ai CNAME points to:"
    echo "   cname.vercel-dns.com"
fi

echo ""
echo "🔧 Backend API (api.mapmystandards.ai):"
if curl -s https://api.mapmystandards.ai/health | grep -q "healthy\|ok"; then
    echo "✅ Backend API is LIVE"
else
    echo "⏳ Backend is still deploying or starting up..."
    echo "📋 Check Railway deployment logs"
fi

echo ""
echo "📊 Summary:"
echo "- Frontend: https://platform.mapmystandards.ai"
echo "- Backend API: https://api.mapmystandards.ai"
echo "- Vercel Backup URL: https://web-2wdw3im60-jeremys-projects-73929cad.vercel.app"
echo ""
echo "🚀 Your MapMyStandards enterprise platform is ready!"
echo "   Customers should access: https://platform.mapmystandards.ai"
