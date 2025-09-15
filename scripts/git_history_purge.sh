#!/usr/bin/env bash
# Purge secrets from git history using git-filter-repo.
# Safe to run multiple times from the repo root. Requires a clean working tree.
#
# What this does:
# - Removes known sensitive files from all history (e.g., .env, frontend/.env, railway.env)
# - Optionally redacts known secret-looking patterns inside history if --redact is passed
# - Prints post-purge guidance for force-pushing and collaborator cleanup
#
# Usage:
#   bash scripts/git_history_purge.sh            # remove files only (fastest, safest)
#   bash scripts/git_history_purge.sh --redact   # also redact patterns in blobs (slower)
#
# Note: You must have git-filter-repo installed:
#   macOS (Homebrew): brew install git-filter-repo
#   pipx: pipx install git-filter-repo
#   pip:  pip install git-filter-repo

set -euo pipefail

if ! command -v git &>/dev/null; then
  echo "git not found in PATH" >&2; exit 1
fi

if ! git rev-parse --git-dir &>/dev/null; then
  echo "Not inside a git repository" >&2; exit 1
fi

if ! command -v git-filter-repo &>/dev/null; then
  echo "git-filter-repo is required. Install with 'brew install git-filter-repo' or 'pipx install git-filter-repo'." >&2
  exit 2
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Working tree is not clean. Commit or stash changes before running." >&2
  exit 3
fi

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "==> Preparing redaction rules"
TMP_REPLACEMENTS=$(mktemp)
cat > "$TMP_REPLACEMENTS" <<'EOF'
***REMOVED***
regex:(sk_live_[A-Za-z0-9_\-]{8,})   sk_live_REDACTED
regex:(sk_test_[A-Za-z0-9_\-]{8,})   sk_test_REDACTED
regex:(sk-proj-[A-Za-z0-9_\-]{8,})   sk-proj-REDACTED
regex:(sk-ant-[A-Za-z0-9_\-]{8,})    sk-ant-REDACTED
regex:(whsec_[A-Za-z0-9]{8,})         whsec_REDACTED
regex:(pk_live_[A-Za-z0-9_\-]{8,})   pk_live_REDACTED
regex:(pk_test_[A-Za-z0-9_\-]{8,})   pk_test_REDACTED
regex:(pcsk_[A-Za-z0-9_\-]{8,})      pcsk_REDACTED
regex:(postmark\w*[_=:\s\"]+[A-Za-z0-9]{16,}) postmark_REDACTED
regex:(OPENAI_API_KEY[=:\s\"]+sk-[A-Za-z0-9_\-]{8,}) OPENAI_API_KEY=sk-REDACTED
regex:(ANTHROPIC_API_KEY[=:\s\"]+sk-ant-[A-Za-z0-9_\-]{8,}) ANTHROPIC_API_KEY=sk-ant-REDACTED
regex:(JWT_SECRET_KEY[=:\s\"]+[A-Za-z0-9_\-]{24,}) JWT_SECRET_KEY=REDACTED
EOF

REMOVE_PATHS=(
  ".env"
  "frontend/.env"
  "railway.env"
  "RAILWAY_BACKEND_ENV.json"
)

echo "==> Removing sensitive files from history"
git filter-repo \
  $(printf -- '--path %q ' "${REMOVE_PATHS[@]}") \
  --invert-paths --force

if [[ "${1:-}" == "--redact" ]]; then
  echo "==> Redacting known secret patterns inside remaining blobs"
  git filter-repo --replace-text "$TMP_REPLACEMENTS" --force
fi

rm -f "$TMP_REPLACEMENTS"

echo "\n==> History rewrite complete. Next steps:" 
cat <<'NEXT'
1) Review locally:
   - git log --oneline --graph --decorate
   - Run scripts/scan_secrets.sh to confirm no obvious secrets remain

2) Force-push to all branches and tags (coordinate with your team):
   - git push --force --all
   - git push --force --tags

3) Ask all collaborators to:
   - git fetch --all --prune
   - Re-clone or run: git reset --hard origin/<branch>; git gc --prune=now --aggressive

4) Rotate any previously exposed credentials (Stripe, Postmark, OpenAI, Anthropic, JWT, etc.).
NEXT

echo "\nDone."
