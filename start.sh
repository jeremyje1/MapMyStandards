#!/bin/sh
# Railway startup script with proper PORT handling and debugging
set -e

echo "Environment variables (filtered):"
env | grep -E 'PORT=|RAILWAY|PYTHON' || true

# Use Railway's PORT or default to 8000
PORT=${PORT:-8000}
if [ -z "$PORT" ]; then
	PORT=8000
fi

echo "Starting server on port: $PORT"

# Test main app import, fallback to test app if still failing
echo "Testing main app import..."
if python -c "import src.a3e.main" 2>/dev/null; then
    echo "✅ Main app imports successfully, launching main app"
    echo "Launching: uvicorn src.a3e.main:app --host 0.0.0.0 --port $PORT"
    exec uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT"
else
    echo "❌ Main app still has import issues, using test app for debugging"
    echo "Launching: uvicorn test_app:app --host 0.0.0.0 --port $PORT"
    exec uvicorn test_app:app --host 0.0.0.0 --port "$PORT"
fi
