#!/bin/bash
set -e

echo "🚀 Starting A³E Administrator Testing Environment"
echo "=================================================="

# Check if credentials exist
if [ ! -f ".env.staging" ]; then
    echo "❌ Staging environment not configured. Run python admin_test_setup.py first"
    exit 1
fi

# Load staging environment
source .env.staging

echo "📋 Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  API Port: $API_PORT" 
echo "  Database: $DATABASE_URL"
echo "  Admin User: $ADMIN_USERNAME"

# Start staging environment
echo "🔧 Starting services..."

# Option 1: Docker Compose
if command -v docker-compose &> /dev/null; then
    echo "🐳 Using Docker Compose..."
    docker-compose -f docker-compose.staging.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo "🔍 Service Status:"
    docker-compose -f docker-compose.staging.yml ps
    
# Option 2: Direct Python
else
    echo "🐍 Starting with Python directly..."
    
    # Start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        echo "  Starting Redis..."
        redis-server --daemonize yes --port 6380
    fi
    
    # Start A³E in staging mode
    export ENVIRONMENT=staging
    python -m src.a3e.main --port 8001 &
    A3E_PID=$!
    
    echo "  A³E started with PID: $A3E_PID"
fi

echo "✅ Staging environment started!"
echo ""
echo "🔗 Access URLs:"
echo "  API: http://localhost:8001"
echo "  Health: http://localhost:8001/health"
echo "  Docs: http://localhost:8001/docs"
echo ""
echo "🔑 Admin Credentials:"
echo "  Username: $ADMIN_USERNAME"
echo "  API Key: $ADMIN_API_KEY"
echo ""
echo "🧪 To run tests:"
echo "  python admin_test_suite.py --api-key $ADMIN_API_KEY"
echo ""
echo "🛑 To stop staging:"
echo "  ./stop_staging.sh"
