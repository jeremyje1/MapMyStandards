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

# Build Tailwind (requires Node). If Node not present, try npx fallback.
if command -v npm >/dev/null 2>&1; then
  if [ -f web/package.json ]; then
    pushd web >/dev/null
    npm install --no-audit --no-fund >/dev/null 2>&1 || true
    # Attempt standard build; fall back to npx if it fails
    if ! npm run build-css >/dev/null 2>&1; then
      echo "⚠️ npm run build-css failed; attempting direct Tailwind build via npx" >&2
      if command -v npx >/dev/null 2>&1; then
        npx tailwindcss -c tailwind.config.js -i src/input.css -o static/css/tailwind.css --minify || \
          echo "⚠️ Tailwind build via npx failed" >&2
      fi
    fi
    popd >/dev/null
  else
    # Fallback: direct npx build when package.json missing but source exists
    if [ -f web/src/input.css ]; then
      echo "ℹ️ web/package.json missing; attempting Tailwind build via npx"
      if command -v npx >/dev/null 2>&1; then
        npx tailwindcss -c web/tailwind.config.js -i web/src/input.css -o web/static/css/tailwind.css --minify || \
          echo "⚠️ Tailwind build via npx failed" >&2
      else
        echo "⚠️ npx not found; cannot build Tailwind CSS" >&2
      fi
    else
      echo "ℹ️ No Tailwind source file; skipping build"
    fi
  fi
else
  # Attempt to use npx if npm isn't available
  if command -v npx >/dev/null 2>&1 && [ -f web/src/input.css ]; then
    echo "⚠️ npm not found; using npx tailwindcss directly"
    npx tailwindcss -c web/tailwind.config.js -i web/src/input.css -o web/static/css/tailwind.css --minify || \
      echo "⚠️ Tailwind build via npx failed" >&2
  else
    echo "⚠️ Neither npm nor npx found; skipping Tailwind build (expect prebuilt web/static/css/tailwind.css)" >&2
  fi
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
sleep 2

echo "🔍 Waiting for frontend health endpoint..."
ATTEMPTS=0
MAX_ATTEMPTS=12
until curl -fsS "http://localhost:$PORT/health/frontend" >/dev/null; do
  ATTEMPTS=$((ATTEMPTS+1))
  if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
    echo "❌ Health check failed after $ATTEMPTS attempts; see $LOG_DIR/main_app.log" >&2
    exit 1
  fi
  echo "⏳ Attempt $ATTEMPTS/$MAX_ATTEMPTS: frontend health not ready yet" >&2
  sleep 1
done
echo "✅ App healthy (frontend health) PID=$PID after $ATTEMPTS attempts"

echo "Deployment complete: http://localhost:$PORT"