#!/bin/bash

echo "🚀 Deploying persistent user settings fix..."

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Fix persistent user settings with database storage

- Created UserSettingsDB service for database-backed storage
- Modified settings API to use database when DATABASE_URL is set
- Falls back to JSON files for local development
- User onboarding data now persists in database on Railway
- Settings include: organization, institution name/type, department, role, accreditor

This fixes the issue where onboarding data was forgotten on each login.
Settings are now stored in the PostgreSQL database instead of ephemeral JSON files.

To complete setup:
1. Deploy this code to Railway
2. Run: railway run python ensure_user_table.py
3. User settings will persist across sessions"

# Push to origin
git push origin main

echo "✅ Persistent settings fix deployed!"
echo ""
echo "📝 Next steps:"
echo "1. Wait for Railway to deploy the new code"
echo "2. Run in Railway: railway run python ensure_user_table.py"
echo "3. This will create/update the users table with onboarding fields"
echo "4. Test onboarding - data should now persist!"
echo ""
echo "🔍 The fix:"
echo "- Onboarding data saves to PostgreSQL database"
echo "- Settings persist across logins and deployments"
echo "- Falls back to JSON files for local development"