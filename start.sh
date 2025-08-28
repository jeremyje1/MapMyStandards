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

# Try to launch main app first
echo "Attempting to launch main app directly..."
if timeout 10s python -c "import src.a3e.main; print('Main app imports OK')" 2>/dev/null; then
    echo "✅ Main app imports successfully"
    echo "Launching: uvicorn src.a3e.main:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 5"
    exec uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT" --timeout-keep-alive 5
else
    echo "❌ Main app import failed or timed out, using test app"
    echo "Launching: uvicorn test_app:app --host 0.0.0.0 --port $PORT"
    exec uvicorn test_app:app --host 0.0.0.0 --port "$PORT"
fi
