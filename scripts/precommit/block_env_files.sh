#!/usr/bin/env bash
set -euo pipefail

changed_files=$(git diff --cached --name-only | grep -E "\.env($|\.)" | grep -v ".env.example" | grep -v ".env.complete.example" || true)

if [[ -n "${changed_files}" ]]; then
  echo "❌ ERROR: Attempting to commit .env file(s)!"
  echo "Files:"
  echo "${changed_files}" | sed 's/^/  - /'
  echo "\nℹ️  Use .env.example or .env.complete.example templates instead."
  exit 1
fi

echo "✅ No .env files staged."
