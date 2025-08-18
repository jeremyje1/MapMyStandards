#!/bin/bash
# Complete deployment script - run after Command Line Tools installation finishes
set -e

echo "=== MapMyStandards Deployment Script ==="
echo "Step 1: Verifying git is available..."

# Check if git works
if ! git --version > /dev/null 2>&1; then
    echo "❌ Git not available. Ensure Command Line Tools installation completed."
    echo "If CLT installation failed, run: xcode-select --install"
    exit 1
fi

echo "✅ Git is working"

echo "Step 2: Configuring git if needed..."
if ! git config user.name > /dev/null 2>&1; then
    echo "Setting up git user configuration..."
    git config --global user.name "Jeremy Estrella"
    git config --global user.email "jeremy.estrella@mapmystandards.ai"
fi

echo "Step 3: Checking remote repository..."
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "Adding remote repository..."
    git remote add origin https://github.com/jeremyje1/MapMyStandards.git
fi

echo "Step 4: Staging files..."
git add -A

echo "Step 5: Committing changes..."
if git diff --cached --quiet; then
    echo "No changes to commit"
else
    git commit -m "chore: canvas fix, vercel config, deploy automation"
    echo "✅ Changes committed"
fi

echo "Step 6: Pushing to GitHub..."
git push -u origin main

echo "Step 7: Deployment options..."
echo "✅ Pushed to GitHub - if GitHub Actions is configured, deployment will start automatically"
echo ""
echo "Manual Vercel deployment options:"
echo "1. Dashboard: Visit vercel.com → project → Deployments → Redeploy"
echo "2. CLI (if Node installed): npx vercel deploy --prod --force"
echo ""
echo "🎉 Deployment script completed!"
