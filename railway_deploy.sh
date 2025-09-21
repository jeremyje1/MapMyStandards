#!/bin/bash

set -euo pipefail

echo "🚀 Deploying MapMyStandards to Railway (browserless)..."

# Configuration (override via env vars if needed)
PROJECT_ID_DEFAULT="4f3575e8-ba3c-4cbb-a566-2dc318c6f58c"
ENV_NAME_DEFAULT="production"
SERVICE_NAME_DEFAULT="MapMyStandards"

PROJECT_ID="${RAILWAY_PROJECT_ID:-$PROJECT_ID_DEFAULT}"
ENV_NAME="${RAILWAY_ENVIRONMENT:-$ENV_NAME_DEFAULT}"
SERVICE_NAME="${RAILWAY_SERVICE_NAME:-$SERVICE_NAME_DEFAULT}"

# Check CLI
if ! command -v railway >/dev/null 2>&1; then
    echo "❌ Railway CLI not installed. Install with: npm install -g @railway/cli"
    exit 1
fi

# Require token for non-interactive login
if [[ -z "${RAILWAY_TOKEN:-}" ]]; then
    echo "❌ RAILWAY_TOKEN not set. Create a token in Railway (Account → Tokens) and run:"
    echo "   export RAILWAY_TOKEN=YOUR_TOKEN"
    echo "Then re-run this script."
    exit 1
fi

echo "🔎 Using project: $PROJECT_ID | env: $ENV_NAME | service: $SERVICE_NAME"

echo "📡 Linking project and service (browserless)..."
# Link project and environment/service context so subsequent commands know where to deploy
railway link "$PROJECT_ID" || true
railway environment "$ENV_NAME" || true
railway service "$SERVICE_NAME" || true

# Deploy (non-interactive)
echo "🚀 Deploying application to Railway..."
railway up --ci --service "$SERVICE_NAME" --environment "$ENV_NAME" --detach || {
    echo "❌ railway up failed"; exit 1; }

echo "✅ Checking deployment status..."
railway status || true

echo "\n🎉 Deployment command finished. For logs:"
echo "   railway logs --project $PROJECT_ID --service $SERVICE_NAME"
echo "   railway open --project $PROJECT_ID"
