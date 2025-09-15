#!/bin/bash

# Set critical environment variables for Railway

echo "Setting Railway environment variables..."

# Core settings
railway variables set ENVIRONMENT=production
railway variables set PYTHONPATH=/app
railway variables set PORT=8000

# JWT and Security
railway variables set JWT_SECRET_KEY="${JWT_SECRET_KEY:?export JWT_SECRET_KEY before running}"
railway variables set SECRET_KEY="BzKxm0pmrXyEyJditsbVDnngbvyhD512-xo0ei5G_l-si4m4B4dsE7DQeF9zYduD1-AtYvvIK-v1fAXS7QjFWQ"
railway variables set JWT_ALGORITHM=HS256
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=30
railway variables set REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration  
railway variables set CORS_ORIGINS="https://mapmystandards.ai,https://www.mapmystandards.ai,https://api.mapmystandards.ai,https://platform.mapmystandards.ai"

# Email settings
railway variables set POSTMARK_API_KEY="${POSTMARK_API_KEY:-your-postmark-key}"
railway variables set POSTMARK_FROM_EMAIL="noreply@mapmystandards.ai"
railway variables set SUPPORT_EMAIL="support@mapmystandards.ai"
railway variables set ADMIN_EMAIL="info@northpathstrategies.org"
railway variables set FROM_EMAIL="info@northpathstrategies.org"

# Storage (AWS S3 - update with your values)
railway variables set STORAGE_PROVIDER=aws
railway variables set AWS_REGION=us-east-1
railway variables set S3_BUCKET=mapmystandards-uploads
# Note: Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY manually in Railway dashboard

# URLs
railway variables set NEXT_PUBLIC_URL=https://mapmystandards.ai
railway variables set NEXT_PUBLIC_API_URL=https://api.mapmystandards.ai
railway variables set API_URL=https://api.mapmystandards.ai

echo "Environment variables set! Please add the following manually in Railway dashboard:"
echo "1. STRIPE_SECRET_KEY"
echo "2. STRIPE_WEBHOOK_SECRET" 
echo "3. AWS_ACCESS_KEY_ID"
echo "4. AWS_SECRET_ACCESS_KEY"
echo "5. POSTMARK_API_KEY (if not set)"
echo "6. ANTHROPIC_API_KEY"
echo "7. OPENAI_API_KEY (if using)"