#!/usr/bin/env python3
"""
Update all login links across the platform to use login-enhanced-v2.html
"""

import os
import re
from pathlib import Path

def update_login_links(filepath):
    """Update login links in a single file"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Count replacements
    replacements = 0
    
    # Patterns to replace
    patterns = [
        (r'href="[^"]*login\.html"', 'href="/login-enhanced-v2.html"'),
        (r'href="[^"]*login-enhanced\.html"', 'href="/login-enhanced-v2.html"'),
        (r'href="/login"', 'href="/login-enhanced-v2.html"'),
        (r'window\.location\.href = "[^"]*login\.html"', 'window.location.href = "/login-enhanced-v2.html"'),
        (r'window\.location\.href = "[^"]*login-enhanced\.html"', 'window.location.href = "/login-enhanced-v2.html"'),
        (r'window\.location\.href = \'/login\'', 'window.location.href = "/login-enhanced-v2.html"'),
        (r'window\.location = "[^"]*login\.html"', 'window.location = "/login-enhanced-v2.html"'),
        (r'window\.location = "[^"]*login-enhanced\.html"', 'window.location = "/login-enhanced-v2.html"'),
    ]
    
    # Apply replacements
    for pattern, replacement in patterns:
        matches = len(re.findall(pattern, content))
        if matches > 0:
            content = re.sub(pattern, replacement, content)
            replacements += matches
    
    # Special case for platform links
    content = content.replace(
        'https://platform.mapmystandards.ai/login-enhanced.html',
        'https://platform.mapmystandards.ai/login-enhanced-v2.html'
    )
    
    # Write back if changes were made
    if replacements > 0 or 'login-enhanced-v2.html' in content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return replacements
    
    return 0

def main():
    """Update all HTML and JS files"""
    
    print("🔄 Updating login links across the platform...\n")
    
    # Directories to scan
    dirs_to_scan = ['web', 'src/a3e/static']
    
    total_files = 0
    total_replacements = 0
    
    for dir_path in dirs_to_scan:
        if not os.path.exists(dir_path):
            print(f"⚠️  Directory not found: {dir_path}")
            continue
            
        # Find all HTML and JS files
        path_obj = Path(dir_path)
        files = list(path_obj.glob('**/*.html')) + list(path_obj.glob('**/*.js'))
        
        for filepath in files:
            # Skip the new login page itself
            if 'login-enhanced-v2.html' in str(filepath):
                continue
                
            replacements = update_login_links(filepath)
            if replacements > 0:
                print(f"✅ Updated {filepath.name}: {replacements} links")
                total_replacements += replacements
                total_files += 1
    
    print(f"\n✨ Updated {total_files} files with {total_replacements} total link replacements")
    
    # List files that might need manual review
    print("\n📋 Files to manually verify:")
    manual_check = [
        "dashboard-enhanced.html",
        "onboarding.html",
        "trial-signup.html",
        "auth-enhanced.js",
        "common.js",
        "ux.js"
    ]
    
    for filename in manual_check:
        print(f"   - {filename}")

if __name__ == "__main__":
    main()