#!/bin/bash

# Clean secrets from git history
echo "Cleaning secrets from git history..."

# Remove the current .env from git tracking
git rm --cached .env 2>/dev/null || true

# Add the cleaned files
git add .env.example .gitignore

# Create a new commit to remove secrets
git commit -m "security: Remove secrets from .env and improve gitignore"

echo "Git history cleaned of secrets!"
echo "The .env file now contains only placeholders."
echo "Your actual secrets are backed up in .env.backup"
