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

# Try launching apps in order of preference
echo "Attempting to launch main app..."
if timeout 5s python -c "import src.a3e.main; print('Main app ready')" 2>/dev/null; then
    echo "✅ Main app imports successfully"
    exec uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT"
else
    echo "❌ Main app failed, trying test app..."
    if python -c "import test_app" 2>/dev/null; then
        echo "✅ Test app available"
        exec uvicorn test_app:app --host 0.0.0.0 --port "$PORT"
    else
        echo "❌ Test app failed, using minimal recovery app"
        exec uvicorn minimal_app:app --host 0.0.0.0 --port "$PORT"
    fi
fi
