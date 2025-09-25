#!/bin/bash

# Platform Consolidation Script
echo "🧹 Starting platform consolidation..."

# Step 1: Backup current main files
echo "📦 Creating backups..."
cp web/dashboard-enhanced.html web/dashboard.html.backup 2>/dev/null || true
cp web/upload-working.html web/upload.html.backup 2>/dev/null || true

# Step 2: Rename main files to standard names
echo "✨ Renaming main files..."
mv web/dashboard-enhanced.html web/dashboard.html 2>/dev/null || echo "Dashboard already renamed"
mv web/upload-working.html web/upload.html 2>/dev/null || echo "Upload already renamed"

# Step 3: Remove old dashboard versions
echo "🗑️  Removing old dashboard versions..."
rm -f web/dashboard-new.html
rm -f web/dashboard-modern.html
rm -f web/dashboard-original.html
rm -f web/dashboard-fixed.html
rm -f web/dashboard-page.html
rm -f web/dashboard-backup.html
rm -f web/dashboard-advanced.html
rm -f web/dashboard-evidence-analysis.html
rm -f web/dashboard_clean.html
rm -f web/dashboard-enhanced.html  # Will be renamed to dashboard.html

# Step 4: Remove old upload versions
echo "🗑️  Removing old upload versions..."
rm -f web/upload_backup.html
rm -f web/upload-fixed.html
rm -f web/upload-modern.html
rm -f web/upload-ai.html
rm -f web/upload_new.html
rm -f web/upload-enhanced.html
rm -f web/upload-enhanced-v2.html
rm -f web/upload-working.html  # Will be renamed to upload.html

# Step 5: Remove duplicate files in root
echo "🗑️  Removing root duplicates..."
rm -f dashboard.html

# Step 6: Clean frontend folder duplicates
echo "🗑️  Cleaning frontend folder..."
rm -rf frontend/public/dashboard*.html
rm -rf frontend/public/upload*.html

echo "✅ Consolidation complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update all references from dashboard-enhanced.html to dashboard.html"
echo "2. Update all references from upload-working.html to upload.html"
echo "3. Fix navigation consistency across all pages"
echo "4. Remove A3E branding references"