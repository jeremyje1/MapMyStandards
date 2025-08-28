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

# Try main app first, fallback to test app if it fails
echo "Attempting to launch main app: src.a3e.main:app"
if ! python -c "import src.a3e.main" 2>/dev/null; then
    echo "❌ Main app import failed, falling back to test app"
    echo "Launching: uvicorn test_app:app --host 0.0.0.0 --port $PORT"
    exec uvicorn test_app:app --host 0.0.0.0 --port "$PORT"
else
    echo "✅ Main app imports successfully"
    echo "Launching: uvicorn src.a3e.main:app --host 0.0.0.0 --port $PORT"
    exec uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT"
fi
