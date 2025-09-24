#!/bin/bash

echo "=== Deploying Backend Documents API to Railway ==="
echo ""
echo "This will deploy the new documents_enhanced.py router with S3 support"
echo ""

# Check if we're in the right directory
if [ ! -f "src/a3e/main.py" ]; then
    echo "Error: Not in the project root directory"
    exit 1
fi

# Add and commit the backend changes
echo "1. Adding backend files to git..."
git add src/a3e/api/routes/documents_enhanced.py
git add src/a3e/api/routes/documents_simple.py
git add src/a3e/main.py

echo ""
echo "2. Creating commit..."
git commit -m "Add enhanced documents API with S3 integration

- Created documents_enhanced.py with full S3 upload/download support
- Added real-time notifications endpoint
- Integrated with existing StorageService
- Fixed imports in documents_simple.py
- Registered new router in main.py"

echo ""
echo "3. Pushing to Railway..."
git push origin main

echo ""
echo "=== Deployment Initiated ==="
echo ""
echo "Railway will automatically deploy the changes."
echo "Monitor the deployment at: https://railway.app/project/prolific-fulfillment"
echo ""
echo "The new endpoints will be available at:"
echo "- POST https://api.mapmystandards.ai/api/documents/upload"
echo "- GET  https://api.mapmystandards.ai/api/documents"
echo "- GET  https://api.mapmystandards.ai/api/documents/{id}"
echo "- GET  https://api.mapmystandards.ai/api/documents/{id}/download"
echo "- DELETE https://api.mapmystandards.ai/api/documents/{id}"
echo "- GET  https://api.mapmystandards.ai/api/documents/notifications"
echo ""
echo "Wait 2-3 minutes for Railway to complete the deployment."