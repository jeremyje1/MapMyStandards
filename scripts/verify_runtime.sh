#!/usr/bin/env bash
set -euo pipefail

# Minimal runtime syntax and import verification for deployment.
# Focus only on active application code; legacy and archived dirs are skipped.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY_BIN="${PY_BIN:-python}"
export PYTHONPATH="$ROOT_DIR/src:${PYTHONPATH:-}"

 echo "[verify] Python: $($PY_BIN -V)"

ACTIVE_GLOBS=(
  "src/a3e/**/*.py"
  "a3e_*.py"
)

echo "[verify] Collecting active python files..."
FILES=$(git ls-files ${ACTIVE_GLOBS[*]} | grep -v '^old_code/' || true)
if [ -z "${FILES:-}" ]; then
    echo "[verify] No active files found; exiting." >&2
    exit 1
fi

# Syntax check
FILE_COUNT=$(echo "$FILES" | wc -w | tr -d ' ')
echo "[verify] Compiling $FILE_COUNT files"
echo "$FILES" | $PY_BIN - <<'EOF'
import py_compile, sys
files = sys.stdin.read().strip().split()
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        print(f"SYNTAX_FAIL {f}: {e}")
        raise
print("[verify] Syntax OK")
EOF

# Targeted import smoke test
cat > /tmp/_import_check.py <<'PY'
CRITICAL_IMPORTS = [
    'fastapi','pydantic','stripe','sqlalchemy','uvicorn'
]
OPTIONAL_IMPORTS = ['a3e.core.config']
failed=[]
for mod in CRITICAL_IMPORTS:
    try:
        __import__(mod)
    except Exception as e:
        failed.append((mod,str(e)))
import os
os.environ.setdefault('SECRET_KEY','dev-test-key')
for mod in OPTIONAL_IMPORTS:
    try:
        __import__(mod)
    except Exception as e:
        failed.append((mod,str(e)))
if failed:
    print('IMPORT_FAIL')
    for m,err in failed:
        print(f" - {m}: {err}")
    raise SystemExit(1)
print('IMPORTS_OK')
PY
$PY_BIN /tmp/_import_check.py

echo "[verify] All runtime checks passed."
