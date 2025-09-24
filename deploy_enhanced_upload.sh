#!/bin/bash

echo "Deploying enhanced upload page to Vercel..."

# Check if we're in the right directory
if [ ! -d "web" ]; then
    echo "Error: web directory not found. Are you in the project root?"
    exit 1
fi

# Deploy to Vercel
echo "Deploying to Vercel..."
cd web

# Check if upload-enhanced-v2.html exists
if [ ! -f "upload-enhanced-v2.html" ]; then
    echo "Error: upload-enhanced-v2.html not found!"
    exit 1
fi

# Deploy
vercel --prod

echo "Deployment complete!"
echo ""
echo "Please test the following URLs:"
echo "1. https://mapmystandards.ai/upload-enhanced-v2.html"
echo "2. https://mapmystandards.ai/dashboard-enhanced.html (check upload links)"
echo ""
echo "Features to test:"
echo "- File drag & drop"
echo "- Upload progress indicators"
echo "- Real-time notifications"
echo "- Document listing"
echo "- S3 file storage integration"