#!/usr/bin/env python3
"""
Quick fix script to update navigation links in HTML files
"""

import os
import re

# Define link replacements
LINK_REPLACEMENTS = {
    # Fix API endpoint references
    'https://api.mapmystandards.ai/auth/login': '/auth/login',
    'https://api.mapmystandards.ai/auth/password-reset': '/auth/password-reset',
    'https://api.mapmystandards.ai/upload': '/upload',
    'https://api.mapmystandards.ai/landing': '/landing',
    'https://api.mapmystandards.ai/docs': '/docs',
    'https://api.mapmystandards.ai/status': '/api',
    
    # Fix navigation links to use relative paths
    'https://mapmystandards.ai/dashboard': '/dashboard',
    './dashboard.html': '/dashboard',
    './login.html': '/login',
    
    # Keep external WordPress links as-is for now (will need to create these pages later)
}

def fix_file(filepath):
    """Fix links in a single file"""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    for old_link, new_link in LINK_REPLACEMENTS.items():
        if old_link in content:
            count = content.count(old_link)
            content = content.replace(old_link, new_link)
            changes_made += count
            print(f"  Replaced {count} instances of {old_link} -> {new_link}")
    
    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Fixed {changes_made} links in {os.path.basename(filepath)}")
    else:
        print(f"  ℹ️  No changes needed in {os.path.basename(filepath)}")
    
    return changes_made

def main():
    """Fix navigation links in all web HTML files"""
    print("🔧 Fixing Navigation Links in MapMyStandards Platform")
    print("="*60)
    
    web_dir = "/Users/jeremy.estrella/Desktop/MapMyStandards-main/web"
    total_changes = 0
    files_fixed = 0
    
    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk(web_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    print(f"Found {len(html_files)} HTML files to check\n")
    
    # Fix each file
    for filepath in html_files:
        changes = fix_file(filepath)
        if changes > 0:
            files_fixed += 1
            total_changes += changes
    
    print("\n" + "="*60)
    print(f"✅ Fixed {total_changes} links across {files_fixed} files")
    
    if total_changes > 0:
        print("\n📋 Next Steps:")
        print("1. Test the updated navigation")
        print("2. Create missing pages (services, about, contact, etc.)")
        print("3. Update the root landing page to be customer-friendly")
        print("4. Implement proper routing for these paths")

if __name__ == "__main__":
    main()
