#!/bin/bash

# Railway startup script with database URL normalization

echo "🚀 Starting A3E on Railway..."

# Check and normalize DATABASE_URL
if [ -n "$DATABASE_URL" ]; then
    echo "✅ DATABASE_URL is set"
    
    # If it starts with postgres:// (Railway format), we're good
    # The Python app will handle the conversion to asyncpg
    if [[ $DATABASE_URL == postgres://* ]]; then
        echo "  Format: postgres:// (Railway standard)"
    elif [[ $DATABASE_URL == postgresql://* ]]; then
        echo "  Format: postgresql://"
    else
        echo "  ⚠️ Unknown database URL format"
    fi
else
    echo "❌ DATABASE_URL not set - using SQLite fallback"
    export DATABASE_URL="sqlite:///./a3e_fallback.db"
fi

# Ensure Python path is set
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Start the application
echo "Starting FastAPI application..."
exec python src/a3e/main_production.py
