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

# Launch main application (logger issue should be fixed)
echo "Launching main app: uvicorn src.a3e.main:app --host 0.0.0.0 --port $PORT"
exec uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT"
