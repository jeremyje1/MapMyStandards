#!/bin/sh
# Railway startup script with proper PORT handling

# Use Railway's PORT or default to 8000
PORT=${PORT:-8000}

echo "Starting server on port: $PORT"

# Start uvicorn with the resolved port
exec uvicorn src.a3e.main:app --host 0.0.0.0 --port $PORT
