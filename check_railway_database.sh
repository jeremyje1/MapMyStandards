#!/bin/bash

echo "🚂 Checking Railway Database Configuration..."
echo "============================================"

# Check if DATABASE_URL exists
echo "🔍 Checking for DATABASE_URL..."
if railway variables | grep -q "DATABASE_URL"; then
    echo "✅ DATABASE_URL is configured!"
    
    # Get the DATABASE_URL value (redacted)
    railway variables | grep "DATABASE_URL" | sed 's/password=[^@]*/password=****/g'
    
    echo ""
    echo "📊 Database Status: READY"
    echo "Your application will automatically use this PostgreSQL database."
else
    echo "❌ DATABASE_URL not found!"
    echo ""
    echo "📋 To add PostgreSQL to your Railway project:"
    echo "1. Go to https://railway.app/dashboard"
    echo "2. Select your 'mapmystandards-prod' project"
    echo "3. Click '+ New' → 'Database' → 'PostgreSQL'"
    echo "4. Railway will automatically inject DATABASE_URL"
    echo ""
    echo "Or use CLI: railway add"
fi

echo ""
echo "🔧 Other Database-Related Variables:"
railway variables | grep -E "(DB_|DATABASE_|POSTGRES_|PG_)" || echo "None found"

echo ""
echo "✅ Check complete!"
