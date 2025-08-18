#!/bin/bash

# A³E System Startup Script
echo "🚀 Starting A³E System..."

# Set the working directory
cd "$(dirname "$0")"

# Check if PostgreSQL is running
if ! pgrep -x "postgres" > /dev/null; then
    echo "❌ PostgreSQL is not running. Please start it first:"
    echo "   brew services start postgresql@14"
    exit 1
fi

# Check if Python 3.9 is available
PYTHON_PATH="/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python 3.9 not found. Using system python3..."
    PYTHON_PATH="python3"
fi

# Kill any existing uvicorn processes
echo "🔄 Stopping any existing servers..."
pkill -f uvicorn 2>/dev/null || true
sleep 2

# Set Python path and start the server
echo "🌟 Starting A³E server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📚 API Documentation at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
PYTHONPATH="$(pwd)/src" "$PYTHON_PATH" -m uvicorn a3e.main:app --host 0.0.0.0 --port 8000 --reload

echo "👋 A³E server stopped."
