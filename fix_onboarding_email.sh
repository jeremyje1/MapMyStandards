#!/bin/bash

echo "🔧 Deploying onboarding email fix..."

# Stage changes
git add -A

# Commit with message
git commit -m "Fix onboarding email detection issue

- Store user email in localStorage/sessionStorage on login
- Use keys that onboarding page expects (a3e_user_email, a3e_pending_email)
- Update logout to preserve email data for better user experience
- Fixes 'We could not detect your signup email' warning

This ensures onboarding can properly save user progress."

# Push to origin
git push origin main

echo "✅ Fix deployed!"
echo ""
echo "The onboarding page should now properly detect the user's email and save progress."