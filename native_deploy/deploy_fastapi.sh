#!/usr/bin/env bash
# Native (non-Docker) deployment script for FastAPI A3E app
set -euo pipefail

APP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_ENV_NAME="a3e_fastapi_env"
PY_VERSION_MIN=3.10
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}
LOG_DIR="$APP_ROOT/logs"
UVICORN_HOST=${HOST:-0.0.0.0}
APP_IMPORT="src.a3e.main:app"

echo "== A3E Native Deployment =="
cd "$APP_ROOT"
mkdir -p "$LOG_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Install Python 3.10+ first." >&2
  exit 1
fi

if [ ! -d "$PY_ENV_NAME" ]; then
  echo "Creating virtual environment: $PY_ENV_NAME"
  python3 -m venv "$PY_ENV_NAME"
fi
source "$PY_ENV_NAME/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r requirements.txt || {
  echo "Failed installing requirements" >&2; exit 1; }

# Ensure gunicorn + uvicorn worker available even if not pinned
python -m pip install gunicorn uvicorn

# Simple health preflight: import app
python - <<'EOF'
import importlib,sys
mod_path="src.a3e.main"
try:
    m=importlib.import_module(mod_path)
    assert hasattr(m,'app'), 'FastAPI app not found in '+mod_path
    print('Preflight import OK')
except Exception as e:
    print('Preflight import FAILED:', e, file=sys.stderr)
    sys.exit(1)
EOF

PID_FILE="$LOG_DIR/fastapi.pid"
if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
  echo "Stopping existing process $(cat $PID_FILE)"
  kill "$(cat $PID_FILE)" || true
  sleep 2
fi

echo "Starting FastAPI (gunicorn+uvicorn worker) on port $PORT"
nohup gunicorn "$APP_IMPORT" \
  -k uvicorn.workers.UvicornWorker \
  -w "$WORKERS" \
  -b "$UVICORN_HOST:$PORT" \
  --timeout 60 \
  --graceful-timeout 30 \
  --access-logfile "$LOG_DIR/access.log" \
  --error-logfile "$LOG_DIR/error.log" \
  --log-level info > "$LOG_DIR/console.out" 2>&1 &
PID=$!
echo $PID > "$PID_FILE"

sleep 3
if curl -fsS "http://127.0.0.1:$PORT/landing" >/dev/null 2>&1; then
  echo "Deployment success: http://127.0.0.1:$PORT/landing"
else
  echo "Health check failed; see logs in $LOG_DIR" >&2
  exit 1
fi
