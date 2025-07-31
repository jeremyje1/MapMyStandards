#!/bin/bash

# Quick Production Start for A³E API
# Starts the application with Gunicorn for production

set -e

echo "🚀 Starting A³E API in Production Mode"
echo "======================================"

# Configuration
WORKERS=${WORKERS:-4}
PORT=${PORT:-8000}
HOST=${HOST:-127.0.0.1}

# Check if we're in the right directory
if [ ! -f "src/a3e/main.py" ]; then
    echo "❌ Error: Please run this script from the MapMyStandards root directory"
    echo "Current directory: $(pwd)"
    echo "Expected files: src/a3e/main.py"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
if command -v poetry &> /dev/null; then
    poetry install --only=main
else
    pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn gunicorn
fi

# Check environment configuration
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found, copying from example..."
    cp .env.example .env
    echo "❗ Please update .env with your production configuration"
fi

# Create log directory
mkdir -p logs

echo "🔧 Production Configuration:"
echo "  Workers: $WORKERS"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  App: src.a3e.main:app"
echo ""

# Start with Gunicorn
echo "🚀 Starting Gunicorn..."
echo "Press Ctrl+C to stop"
echo ""

exec gunicorn \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind $HOST:$PORT \
    --timeout 30 \
    --keepalive 2 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level info \
    --name "a3e-api" \
    src.a3e.main:app
