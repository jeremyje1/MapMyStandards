#!/usr/bin/env bash
set -euo pipefail

TARGET_ENV=${1:-production}
echo "Adding Vercel env vars to $TARGET_ENV";

vercel env add NEXT_PUBLIC_APP_URL "$TARGET_ENV"
vercel env add NEXTAUTH_SECRET "$TARGET_ENV"
vercel env add POSTMARK_API_TOKEN "$TARGET_ENV"
vercel env add POSTMARK_MESSAGE_STREAM "$TARGET_ENV"
vercel env add FROM_EMAIL "$TARGET_ENV"
vercel env add REPLY_TO_EMAIL "$TARGET_ENV"
vercel env add STRIPE_PUBLISHABLE_KEY "$TARGET_ENV"
vercel env add STRIPE_PRICE_DEPARTMENT_ANNUAL "$TARGET_ENV"
vercel env add STRIPE_PRICE_CAMPUS_ANNUAL "$TARGET_ENV"
vercel env add STRIPE_PRICE_SYSTEM_ANNUAL "$TARGET_ENV"
vercel env add STRIPE_PRICE_PILOT "$TARGET_ENV"

echo "Done. Review in Vercel dashboard.";
