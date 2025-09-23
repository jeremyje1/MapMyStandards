#!/bin/bash

echo "🚀 Deploying routing and flow fixes..."

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Fix routing issues preventing proper authentication flow

- Add /login route rewrite in vercel.json to point to login-enhanced.html
- Add redirects for old login pages (login.html, login-platform.html)
- Update old dashboard.html to redirect to dashboard-enhanced.html
- Update old login pages to redirect to enhanced versions
- Preserve query parameters (like return URL) during redirects

This fixes the issue where clicking dashboard redirected to old login page
and broke the authentication flow."

# Push to origin
git push origin main

echo "✅ Routing fixes deployed!"
echo ""
echo "📝 Summary of changes:"
echo "1. /login now routes to /login-enhanced.html"
echo "2. Old dashboard redirects to enhanced dashboard"
echo "3. Old login pages redirect to enhanced login"
echo "4. Query parameters are preserved during redirects"
echo ""
echo "The flow should now work properly:"
echo "Upload → Click Dashboard → Stay in enhanced flow → No unexpected redirects"