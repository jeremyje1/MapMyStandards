#!/bin/bash

echo "🚀 Deploying navigation and authentication fixes..."

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Fix navigation flow and authentication issues

- Fixed all navigation links to point to enhanced pages consistently
- Fixed onboarding redirect after completion (was going to old dashboard)
- Fixed logout function to preserve onboarding status
- Added clear instructions on upload page for next steps
- Updated 'What's Next' section to redirect to dashboard-enhanced.html
- Set onboarding flag on successful login for existing users
- Fixed navigation menu links on all enhanced pages

This resolves the issue where users were being logged out unexpectedly
when clicking navigation links and being sent back to onboarding."

# Push to origin
git push origin main

echo "✅ Changes pushed to repository"
echo ""
echo "📝 Summary of fixes:"
echo "1. All navigation now uses enhanced pages (dashboard-enhanced.html, upload-enhanced.html)"
echo "2. Onboarding completion now redirects to dashboard-enhanced.html"
echo "3. Logout preserves onboarding status (only clears auth tokens)"
echo "4. Upload page shows clear next steps with guidance"
echo "5. Navigation between pages no longer triggers unexpected logouts"
echo ""
echo "🧪 Please test the flow again with your test user!"