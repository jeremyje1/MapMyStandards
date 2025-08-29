#!/bin/bash

# Production startup script for Railway
# Handles database migrations and server startup

set -e

echo "🚀 Starting MapMyStandards Production Server"
echo "==========================================="

# Export Python path
export PYTHONPATH=/app:$PYTHONPATH

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python3 << EOF
import time
import os
from sqlalchemy import create_engine

db_url = os.getenv('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    # Fix for SQLAlchemy (Railway uses postgres:// but SQLAlchemy needs postgresql://)
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
    os.environ['DATABASE_URL'] = db_url

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        engine = create_engine(db_url)
        connection = engine.connect()
        connection.close()
        print("✅ Database connection successful!")
        break
    except Exception as e:
        retry_count += 1
        print(f"Attempt {retry_count}/{max_retries}: Database not ready, waiting...")
        time.sleep(2)
else:
    print("❌ Could not connect to database after 60 seconds")
    exit(1)
EOF

# Run database migrations
echo "🔄 Running database migrations..."
if [ -f "alembic.ini" ]; then
    # Update alembic to use DATABASE_URL from environment
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql:\/\/}"
    alembic upgrade head || echo "⚠️  Migration failed or already up to date"
else
    echo "⚠️  No alembic.ini found, skipping migrations"
fi

# Initialize database tables if needed
echo "📊 Initializing database schema..."
python3 << EOF
import os
import sys
sys.path.insert(0, '/app')

# Fix DATABASE_URL for SQLAlchemy if needed
db_url = os.getenv('DATABASE_URL', '')
if db_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = db_url.replace('postgres://', 'postgresql://', 1)

try:
    from src.a3e.database.connection import init_db
    init_db()
    print("✅ Database schema initialized")
except Exception as e:
    print(f"⚠️  Database initialization: {e}")
EOF

# Start the FastAPI application
echo "🌐 Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn src.a3e.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 1 \
    --log-level info