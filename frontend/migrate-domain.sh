#!/bin/bash
# Frontend Domain Migration Script
# From Railway to Vercel

echo "🔄 Frontend Domain Migration: Railway → Vercel"
echo "=============================================="
echo ""

echo "📋 Migration Steps:"
echo "1. Remove platform.mapmystandards.ai from Railway (manual)"
echo "2. Add platform.mapmystandards.ai to Vercel (automated)"
echo "3. Update DNS to point to Vercel (manual)"
echo "4. Delete Railway frontend project (optional)"
echo ""

read -p "Have you removed platform.mapmystandards.ai from Railway? (y/n): " removed_from_railway

if [ "$removed_from_railway" = "y" ]; then
    echo "✅ Adding platform.mapmystandards.ai to Vercel..."
    vercel domains add platform.mapmystandards.ai
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Domain successfully added to Vercel!"
        echo ""
        echo "📝 Next steps:"
        echo "1. Update DNS A record: platform.mapmystandards.ai → 76.76.21.21"
        echo "2. Wait for DNS propagation (up to 24 hours)"
        echo "3. Vercel will automatically provision SSL certificate"
        echo ""
        echo "🗑️  Optional: Delete Railway frontend project"
        echo "   Go to Railway dashboard → Project Settings → Delete Project"
        echo ""
        echo "🎉 Migration complete!"
    else
        echo "❌ Failed to add domain to Vercel. Check if it's still assigned to Railway."
    fi
else
    echo "⏸️  Please remove platform.mapmystandards.ai from Railway first:"
    echo "   1. Go to: https://railway.com/project/1a6b310c-fa1b-43ee-96bc-e093cf175829"
    echo "   2. Click MapMyStandards service → Settings → Domains"
    echo "   3. Remove platform.mapmystandards.ai"
    echo "   4. Run this script again"
fi
