# Secrets cleanup and rotation

This repo previously contained plaintext secrets in committed files (e.g., `railway.env`, `frontend/.env`). Follow these steps to remediate:

1) Rotate all exposed keys immediately
- Stripe: rotate STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET
- Postmark: rotate POSTMARK_API_TOKEN
- OpenAI: rotate OPENAI_API_KEY
- Anthropic: rotate ANTHROPIC_API_KEY
- Pinecone: rotate PINECONE_API_KEY
- JWT: generate a new 64+ char JWT_SECRET_KEY

2) Purge secrets from git history
- Prefer git filter-repo (faster, safer). Install: `brew install git-filter-repo`.
- Remove files from history:
  - railway.env
  - frontend/.env
  - any other secret snapshots
- Example command:

  git filter-repo --path railway.env --path frontend/.env --invert-paths

- Force-push to remote branches (coordinate with collaborators):

  git push --force --all
  git push --force --tags

3) Verify cleanup with a fresh clone
- Clone to a new folder and scan for patterns:
  - sk_live|sk_test|whsec_|OPENAI_API_KEY|ANTHROPIC_API_KEY|POSTMARK_API_TOKEN|JWT_SECRET_KEY

4) Prevent recurrence
- .gitignore now blocks .env and railway files
- Use .env.example and frontend/.env.example as templates
- Only set real values in Vercel/Railway env dashboards or local untracked .env

Notes
- History rewrite impacts forks and PRs. Communicate before forcing pushes.
- If filter-repo is unavailable, BFG Repo-Cleaner is an alternative.

---

Quick start with the provided script
- Ensure a clean working tree (no uncommitted changes)
- Install git-filter-repo (macOS: brew install git-filter-repo)
- From repo root:
  - Remove sensitive files from all history (fastest):
    - bash scripts/git_history_purge.sh
  - Also redact common secret patterns (slower):
    - bash scripts/git_history_purge.sh --redact
- Verify: bash scripts/scan_secrets.sh
- Force push: git push --force --all && git push --force --tags
- Ask collaborators to re-clone or hard-reset and run git gc --prune=now --aggressive