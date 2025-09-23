#!/bin/bash

echo "🚀 Deploying complete upload flow fixes..."

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Fix complete upload flow and navigation issues

- Enhanced upload success modal with prominent next step guidance
- Added backdrop overlay for better visibility
- Fixed ALL navigation links to use enhanced pages consistently
- Fixed dashboard empty state links (/upload → /upload-enhanced.html)
- Fixed navigation functions (upload-modern → upload-enhanced.html)
- Fixed standards navigation to stay within enhanced flow
- Added 'Upload more files' option in success modal

This ensures:
1. Clear guidance after file upload
2. No unexpected logouts when navigating
3. All navigation stays within enhanced flow
4. Better user experience with modal overlay"

# Push to origin
git push origin main

echo "✅ Complete upload flow fixes deployed!"
echo ""
echo "📝 The flow should now work as:"
echo "1. Upload files → See prominent success modal"
echo "2. Click 'Continue to Dashboard' → Go to enhanced dashboard"
echo "3. Navigate between pages → Stay logged in"
echo "4. All links point to correct enhanced pages"
echo ""
echo "Documents are being saved on the backend - check the dashboard metrics to confirm."