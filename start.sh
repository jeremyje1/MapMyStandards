#!/bin/sh
# Railway startup script with proper PORT handling and debugging
# Remove set -e to prevent script exit on individual command failures

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
echo "Testing main app import..."
if python3 -c "import src.a3e.main; print('✅ Main app ready')" 2>&1; then
    echo "✅ Main app imports successfully, starting full A³E platform..."
    exec python3 -m uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT"
else
    echo "❌ Main app import failed, checking emergency app..."
fi

echo "⚠️ Main app failed, falling back to emergency mode..."

# Emergency app fallback has no dependencies
echo "Testing emergency app import..."
if python3 -c "import emergency_app; print('✅ Emergency app ready')" 2>&1; then
    echo "✅ Emergency app imports successfully, starting emergency mode..."
    exec python3 -m uvicorn emergency_app:app --host 0.0.0.0 --port "$PORT"
else
    echo "❌ Emergency app import also failed"
fi

echo "❌ All apps failed - this should not happen"
exit 1
