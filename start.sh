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

# Multi-tier startup strategy - try main app first, then fallbacks
echo "STARTUP: Attempting main application..."

# Try main app first (full platform functionality)
if python3 -c "import src.a3e.main; print('✅ Main app ready')" 2>/dev/null; then
    echo "✅ Starting full A³E platform with all features..."
    exec python3 -m uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT"
fi

echo "⚠️ Main app failed, falling back to emergency mode..."

# Emergency app fallback has no dependencies
if python3 -c "import emergency_app" 2>/dev/null; then
    echo "✅ Emergency app starting (limited functionality)..."
    exec python3 -m uvicorn emergency_app:app --host 0.0.0.0 --port "$PORT"
fi

echo "❌ All apps failed - this should not happen"
exit 1
