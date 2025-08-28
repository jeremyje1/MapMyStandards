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

# Emergency startup - try simplest apps first
echo "EMERGENCY MODE: Starting simplest possible app..."

# Emergency app has no dependencies
if python -c "import emergency_app" 2>/dev/null; then
    echo "✅ Emergency app starting..."
    exec uvicorn emergency_app:app --host 0.0.0.0 --port "$PORT"
fi

echo "❌ All apps failed - this should not happen"
exit 1
