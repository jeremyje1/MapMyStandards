#!/usr/bin/env bash
set -euo pipefail

vars=(
  STRIPE_SECRET_KEY
  STRIPE_WEBHOOK_SECRET
  POSTMARK_API_TOKEN
  SENDGRID_API_KEY
  DATABASE_URL
  NEXTAUTH_SECRET
  FROM_EMAIL
  REPLY_TO_EMAIL
  POSTMARK_MESSAGE_STREAM
  STRIPE_PRICE_DEPARTMENT_ANNUAL
  STRIPE_PRICE_CAMPUS_ANNUAL
  STRIPE_PRICE_SYSTEM_ANNUAL
  STRIPE_PRICE_PILOT
)

for v in "${vars[@]}"; do
  if [ -z "${!v:-}" ]; then
    echo "[WARN] $v not set; skipping" >&2
    continue
  fi
  railway variables set "$v"="${!v}"

done

echo "Railway env sync complete.";
