#!/usr/bin/env bash
set -euo pipefail

# Helper script: stages current changes, commits, pushes, and (optionally) triggers Vercel deploy via GitHub Action.
# Usage:
#   bash scripts/commit_and_deploy_vercel.sh "chore: update config" [branch]
# Default branch: main

MSG=${1:-"chore: update"}
BRANCH=${2:-"main"}

if ! command -v git >/dev/null 2>&1; then
  echo "git not available. Install Command Line Tools first (xcode-select --install)." >&2
  exit 1
fi

echo "Staging tracked and new files..."
git add -A

if git diff --cached --quiet; then
  echo "No changes to commit.";
else
  echo "Committing..."
  git commit -m "$MSG"
fi

echo "Pushing to origin/$BRANCH..."
git push origin "$BRANCH"

echo "If GitHub Action for Vercel is configured, deployment will start automatically."
