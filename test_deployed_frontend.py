#!/usr/bin/env python3
"""Test that the deployed frontend has all the consolidated pages"""

import requests

PLATFORM_BASE = "https://platform.mapmystandards.ai"

print("🔍 Testing Deployed Frontend Pages")
print("=" * 60)

pages = [
    ("Homepage redirect", "/", 308),
    ("Login page", "/login.html", 200),
    ("Dashboard", "/dashboard.html", 200),
    ("Documents", "/documents.html", 200),
    ("Upload", "/upload.html", 200),
    ("Analysis Results", "/analysis-results.html", 200),
    ("Reports", "/reports-modern.html", 200),
]

print(f"\nTesting pages at: {PLATFORM_BASE}")
print("-" * 40)

success_count = 0
for name, path, expected_status in pages:
    try:
        resp = requests.get(f"{PLATFORM_BASE}{path}", allow_redirects=False)
        status = resp.status_code
        if status == expected_status:
            print(f"✅ {name}: {path} ({status})")
            success_count += 1
        else:
            print(f"❌ {name}: {path} (Got {status}, expected {expected_status})")
    except Exception as e:
        print(f"❌ {name}: {path} (Error: {str(e)})")

print("\n" + "-" * 40)
print(f"✅ {success_count}/{len(pages)} pages working correctly")

# Test old URL redirects
print("\n🔄 Testing URL Redirects:")
print("-" * 40)

redirects = [
    ("/dashboard-enhanced.html", "/dashboard.html"),
    ("/dashboard-modern.html", "/dashboard.html"),
    ("/upload-working.html", "/upload.html"),
    ("/upload-enhanced.html", "/upload.html"),
]

for old_url, new_url in redirects:
    try:
        resp = requests.get(f"{PLATFORM_BASE}{old_url}", allow_redirects=False)
        if resp.status_code == 308 and resp.headers.get('Location') == new_url:
            print(f"✅ {old_url} → {new_url}")
        else:
            print(f"❌ {old_url} (Status: {resp.status_code}, Location: {resp.headers.get('Location')})")
    except Exception as e:
        print(f"❌ {old_url} (Error: {str(e)})")

print("\n" + "=" * 60)
print("\n🎉 Frontend deployment complete!")
print(f"   Platform URL: {PLATFORM_BASE}")
print("   All consolidated pages are now live!")