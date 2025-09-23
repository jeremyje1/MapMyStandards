#!/bin/bash

echo "🚀 Deploying S3 upload fix..."

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Fix document uploads with AWS S3 storage

- Replaced local file storage with AWS S3/cloud storage
- Added proper file content validation (skip 0 byte files)
- Generate unique storage keys for each upload
- Store metadata with each file
- Return storage type in upload response

This fixes the 0 bytes issue on Railway deployment.
Documents will now persist properly in S3.

Required env vars on Railway:
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- AWS_REGION
- S3_BUCKET_NAME

See AWS_S3_UPLOAD_SETUP.md for configuration guide."

# Push to origin
git push origin main

echo "✅ S3 upload fix deployed!"
echo ""
echo "⚠️  IMPORTANT: Add these environment variables to Railway:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo "   - AWS_REGION (default: us-east-1)"
echo "   - S3_BUCKET_NAME (or it will use 'mapmystandards-uploads')"
echo ""
echo "📖 See AWS_S3_UPLOAD_SETUP.md for full setup instructions"