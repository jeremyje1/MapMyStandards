#!/bin/bash
set -euo pipefail

echo "🚀 Deploying Main FastAPI App (src.a3e.main:app) with Tailwind build"

PY_ENV=${PY_ENV:-".venv"}
PORT=${PORT:-8000}

if [ ! -d web ]; then
  echo "❌ web directory missing; aborting" >&2
  exit 1
fi

if [ ! -d "$PY_ENV" ]; then
  python3 -m venv "$PY_ENV"
fi
source "$PY_ENV/bin/activate"
pip install --upgrade pip >/dev/null
if [ -f requirements.txt ]; then
  pip install -r requirements.txt >/dev/null
else
  pip install fastapi uvicorn >/dev/null
fi

# Build Tailwind (requires Node). If Node not present, warn and continue (CSS may be stale)
if command -v npm >/dev/null 2>&1; then
  if [ -f web/package.json ]; then
    pushd web >/dev/null
    npm install --no-audit --no-fund >/dev/null 2>&1 || true
    npm run build-css || { echo "⚠️ Tailwind build failed; using existing CSS" >&2; }
    popd >/dev/null
  else
    echo "ℹ️ No web/package.json; skipping Tailwind build"
  fi
else
  echo "⚠️ npm not found; skipping Tailwind build (expect prebuilt web/static/css/tailwind.css)" >&2
fi

CSS_FILE="web/static/css/tailwind.css"
if [ ! -f "$CSS_FILE" ]; then
  echo "❌ Missing $CSS_FILE after build; aborting" >&2
  exit 1
fi
SIZE=$(wc -c < "$CSS_FILE")
if [ "$SIZE" -lt 5000 ]; then
  echo "❌ $CSS_FILE too small ($SIZE bytes)" >&2
  exit 1
fi
echo "✅ tailwind.css present ($SIZE bytes)"

echo "🔄 Stopping existing uvicorn (if any)"
pkill -f "uvicorn src.a3e.main:app" 2>/dev/null || true
sleep 1

LOG_DIR=logs
mkdir -p "$LOG_DIR"
echo "▶️  Starting uvicorn on :$PORT"
nohup uvicorn src.a3e.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_DIR/main_app.log" 2>&1 &
PID=$!
sleep 3

if curl -fsS "http://localhost:$PORT/health/frontend" >/dev/null; then
  echo "✅ App healthy (frontend health) PID=$PID"
else
  echo "⚠️ Health check failed; see $LOG_DIR/main_app.log" >&2
  exit 1
fi

echo "Deployment complete: http://localhost:$PORT"