#!/bin/bash

# Script to set CORS_ORIGINS environment variable in Railway

echo "Setting CORS_ORIGINS environment variable in Railway..."

# The CORS origins we need to allow
CORS_ORIGINS="https://platform.mapmystandards.ai,https://api.mapmystandards.ai,https://mapmystandards.ai,https://www.mapmystandards.ai,https://app.mapmystandards.ai,http://localhost:3000,http://localhost:3001,http://localhost:8000"

echo "CORS_ORIGINS value: $CORS_ORIGINS"
echo ""
echo "Please run this command in your Railway project:"
echo ""
echo "railway variables set CORS_ORIGINS=\"$CORS_ORIGINS\""
echo ""
echo "Or add it manually in the Railway dashboard under Variables section."