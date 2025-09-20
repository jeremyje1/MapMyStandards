#!/usr/bin/env bash
set -euo pipefail

# Quick BYOL corpus reload + status check
# Usage:
#   BASE_URL=https://api.mapmystandards.ai TOKEN=<JWT> ./scripts/byol_status_check.sh

BASE_URL=${BASE_URL:-https://api.mapmystandards.ai}
TOKEN=${TOKEN:-}

if [[ -z "$TOKEN" ]]; then
  echo "TOKEN is required (Bearer JWT)" >&2
  exit 1
fi

echo "== Reload BYOL corpus (GET) =="
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/user/intelligence-simple/standards/byol/reload" | sed -e 's/"token":"[^"]\+"/"token":"***REDACTED***"/' | head -n 200

echo "\n== Corpus Status (primary path) =="
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/user/intelligence-simple/standards/corpus/status" | head -n 200

echo "\n== Corpus Status (aliases) =="
for p in \
  "/api/user/intelligence-simple/standards/status" \
  "/api/user/intelligence-simple/standards/corpusstatus"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$BASE_URL$p")
  echo "$p -> $code"
done

echo "\n== Standards List (limit 1) =="
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE_URL/api/user/intelligence-simple/standards/list?limit=1" | head -n 200

echo "\nDone."
