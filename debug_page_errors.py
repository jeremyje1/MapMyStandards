#!/usr/bin/env python3
"""
Debug what error messages are appearing on pages
"""

import requests

pages = [
    ("homepage-enhanced.html", "Homepage"),
    ("login-enhanced-v2.html", "Login"),
    ("dashboard-enhanced.html", "Dashboard"),
    ("standards-graph-enhanced.html", "Standards Graph"),
    ("onboarding.html", "Onboarding")
]

print("🔍 DEBUGGING PAGE ERROR MESSAGES\n")

for page_file, page_name in pages[:3]:  # Check first 3 pages
    url = f"https://platform.mapmystandards.ai/{page_file}"
    print(f"\n📄 Checking {page_name}: {url}")
    print("-" * 50)
    
    try:
        response = requests.get(url, timeout=10)
        content = response.text.lower()
        
        # Look for specific error patterns
        error_patterns = [
            ("404", "404 error"),
            ("not found", "Not found error"),
            ("error:", "Error message"),
            ("failed to", "Failed operation"),
            ("cannot", "Cannot message"),
            ("unable to", "Unable message"),
            ("access denied", "Access denied"),
            ("unauthorized", "Unauthorized")
        ]
        
        found_errors = []
        for pattern, desc in error_patterns:
            if pattern in content:
                # Find context around error
                pos = content.find(pattern)
                start = max(0, pos - 50)
                end = min(len(content), pos + 100)
                context = response.text[start:end]
                found_errors.append((desc, context.strip()))
        
        if found_errors:
            print(f"❌ Found {len(found_errors)} error indicator(s):")
            for desc, context in found_errors[:2]:  # Show first 2
                print(f"\n   {desc}:")
                print(f"   Context: ...{context}...")
        else:
            print("✅ No obvious error messages found")
            
        # Check if it's actually a proper HTML page
        if "<html" not in content or "<body" not in content:
            print("⚠️  Page might not be proper HTML")
            
    except Exception as e:
        print(f"❌ Failed to load: {e}")

print("\n" + "="*50)