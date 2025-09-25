#!/usr/bin/env python3
"""Update all references to consolidated file names"""

import os
import re

def update_file_references(filepath):
    """Update references in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update dashboard references
        content = re.sub(r'dashboard-enhanced\.html', 'dashboard.html', content)
        content = re.sub(r'dashboard-modern\.html', 'dashboard.html', content)
        content = re.sub(r'dashboard-new\.html', 'dashboard.html', content)
        
        # Update upload references
        content = re.sub(r'upload-working\.html', 'upload.html', content)
        content = re.sub(r'upload-enhanced\.html', 'upload.html', content)
        content = re.sub(r'upload-enhanced-v2\.html', 'upload.html', content)
        
        # Update A3E references to MapMyStandards
        content = re.sub(r'a3e_api_key', 'access_token', content)
        content = re.sub(r'a3e_user_email', 'user_email', content)
        content = re.sub(r'a3e_', 'mms_', content)  # Generic A3E prefix
        content = re.sub(r'A3E', 'MapMyStandards', content)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
    return False

def main():
    """Update all HTML files in web directory"""
    updated_files = []
    web_dir = 'web'
    
    print("🔍 Scanning files...")
    
    for filename in os.listdir(web_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(web_dir, filename)
            if update_file_references(filepath):
                updated_files.append(filename)
                print(f"✅ Updated: {filename}")
    
    print(f"\n📊 Updated {len(updated_files)} files")
    
    # Also update the main routing file
    print("\n🔧 Updating API routes...")
    api_file = 'src/a3e/main.py'
    if os.path.exists(api_file):
        if update_file_references(api_file):
            print(f"✅ Updated: {api_file}")

if __name__ == "__main__":
    main()