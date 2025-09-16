#!/usr/bin/env bash
set -euo pipefail

echo "== MapMyStandards Prod UI Smoke Test =="

# Defaults
: "${MMS_BASE:=https://platform.mapmystandards.ai}"
echo "Base URL: ${MMS_BASE}"

have_node=$(command -v node || true)
if [ -z "$have_node" ]; then
  echo "Node.js not found. Please install Node 18+." >&2
  exit 1
fi

# Prompt for auth if not provided via env
if [ -z "${MMS_API_KEY:-}" ] && [ -z "${MMS_JWT:-}" ]; then
  echo "Provide ONE of the following (leave the other blank):"
  read -s -r -p "API key (hidden, optional): " MMS_API_KEY || true; echo
  read -s -r -p "JWT token (hidden, optional): " MMS_JWT || true; echo
fi

# Optional UI login fallback
if [ -z "${MMS_API_KEY:-}" ] && [ -z "${MMS_JWT:-}" ]; then
  echo "No API key or JWT provided. UI login fallback:"
  read -r -p "Test user email (optional): " TEST_USER_EMAIL || true
  read -s -r -p "Test user password (hidden, optional): " TEST_USER_PASSWORD || true; echo
fi

export MMS_BASE
[ -n "${MMS_API_KEY:-}" ] && export MMS_API_KEY
[ -n "${MMS_JWT:-}" ] && export MMS_JWT
[ -n "${TEST_USER_EMAIL:-}" ] && export TEST_USER_EMAIL
[ -n "${TEST_USER_PASSWORD:-}" ] && export TEST_USER_PASSWORD

# Optional S3 upload is picked up from existing env (AWS_* and bucket vars)

echo "Running smoke test..."
node scripts/prod_smoke_test.mjs

echo "\nArtifacts (if local):"
ls -1 artifacts || true

if [ -n "${MMS_ARTIFACTS_BUCKET:-${S3_BUCKET:-}}" ] && command -v aws >/dev/null 2>&1; then
  BUCKET="${MMS_ARTIFACTS_BUCKET:-${S3_BUCKET}}"
  echo "\nRecent S3 uploads (if any):"
  aws s3 ls "s3://${BUCKET}/smoke-tests/" --recursive | tail -n 10 || true
fi

echo "Done."
