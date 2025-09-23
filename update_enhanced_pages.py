#!/usr/bin/env python3
"""
Update all enhanced pages with common.js and improved error handling
"""

import os
import re
from pathlib import Path

def update_page(filepath):
    """Update a single HTML page with common.js"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if common.js is already included
    if 'common.js' in content:
        print(f"✅ {os.path.basename(filepath)} already includes common.js")
        return False
    
    # Find the first script tag or the end of head tag
    script_match = re.search(r'<script', content)
    head_match = re.search(r'</head>', content)
    
    if script_match:
        # Insert before the first script tag
        insert_pos = script_match.start()
        indent = "    "
    elif head_match:
        # Insert before closing head tag
        insert_pos = head_match.start()
        indent = "    "
    else:
        print(f"❌ Could not find insertion point in {os.path.basename(filepath)}")
        return False
    
    # Create the common.js script tag
    common_script = f'{indent}<script src="js/common.js"></script>\n'
    
    # Insert the script tag
    new_content = content[:insert_pos] + common_script + content[insert_pos:]
    
    # Write the updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Updated {os.path.basename(filepath)}")
    return True

def add_loading_states(filepath):
    """Add loading state handling to API calls"""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find fetch calls without loading states
    fetch_pattern = r'fetch\([^)]+\)(?!.*showLoading)'
    
    # Count matches
    matches = len(re.findall(fetch_pattern, content))
    if matches > 0:
        print(f"   📊 Found {matches} fetch calls that could use loading states")

def main():
    """Update all enhanced pages"""
    
    web_dir = Path("web")
    if not web_dir.exists():
        print("❌ web directory not found")
        return
    
    # List of enhanced pages to update
    enhanced_pages = [
        "dashboard-enhanced.html",
        "standards-graph-enhanced.html",
        "compliance-dashboard-enhanced.html",
        "reports-enhanced.html",
        "organizational-enhanced.html",
        "settings-enhanced.html",
        "about-enhanced.html",
        "contact-enhanced.html",
        "onboarding.html",
        "trial-signup.html"
    ]
    
    print("🚀 Updating enhanced pages with common.js...\n")
    
    updated_count = 0
    for page in enhanced_pages:
        filepath = web_dir / page
        if filepath.exists():
            if update_page(filepath):
                updated_count += 1
                add_loading_states(filepath)
        else:
            print(f"⚠️  {page} not found")
    
    print(f"\n✨ Updated {updated_count} pages")
    
    # Additional improvements we could make
    print("\n📝 Additional improvements to implement:")
    print("1. Add showLoading() to all API calls")
    print("2. Replace alert() with showAlert() for better UX")
    print("3. Add initMobileMenu() to all pages")
    print("4. Implement proper error boundaries")
    print("5. Add retry logic for failed requests")

if __name__ == "__main__":
    main()