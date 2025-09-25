#!/usr/bin/env python3
"""Test both dashboards to compare functionality and user experience"""

import requests
import json
import time
from urllib.parse import urljoin

API_BASE = "https://api.mapmystandards.ai"
PLATFORM_BASE = "https://platform.mapmystandards.ai"

print("🔍 Dashboard Comparison Analysis")
print("=" * 60)

# 1. Login first
print("\n1. Logging in...")
response = requests.post(f"{API_BASE}/api/auth/login", json={
    "email": "jeremy.estrella@gmail.com",
    "password": "Ipo4Eva45*"
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    exit(1)

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Login successful")

# 2. Test API endpoints
print("\n2. Testing API Endpoints:")

endpoints = [
    ("Documents List", "GET", "/api/user/intelligence-simple/documents/list"),
    ("User Info", "GET", "/api/auth/me"),
    ("Upload Endpoint", "OPTIONS", "/api/user/intelligence-simple/documents/upload"),
    ("Standards", "GET", "/api/standards/all"),
]

api_results = {}
for name, method, endpoint in endpoints:
    try:
        if method == "GET":
            resp = requests.get(f"{API_BASE}{endpoint}", headers=headers)
        else:
            resp = requests.options(f"{API_BASE}{endpoint}", headers=headers)
        api_results[name] = {
            "status": resp.status_code,
            "ok": resp.status_code in [200, 204]
        }
        print(f"   {name}: {'✓' if api_results[name]['ok'] else '✗'} ({resp.status_code})")
    except Exception as e:
        api_results[name] = {"status": "error", "ok": False}
        print(f"   {name}: ✗ (Error: {str(e)})")

# 3. Check available dashboards
print("\n3. Checking Available Dashboards:")

dashboard_pages = [
    ("MapMyStandards Dashboard", "/dashboard.html"),
    ("Enhanced Dashboard", "/dashboard-enhanced.html"),
    ("Modern Dashboard", "/dashboard-modern.html"),
    ("A3E Dashboard", "/a3e-dashboard.html"),
    ("Evidence Analysis Dashboard", "/dashboard-evidence-analysis.html"),
]

working_dashboards = []
for name, path in dashboard_pages:
    try:
        resp = requests.get(f"{PLATFORM_BASE}{path}", allow_redirects=False)
        if resp.status_code == 200:
            working_dashboards.append((name, path))
            print(f"   {name}: ✓ Found")
        else:
            print(f"   {name}: ✗ ({resp.status_code})")
    except:
        print(f"   {name}: ✗ (Error)")

# 4. Check upload pages
print("\n4. Checking Upload Pages:")

upload_pages = [
    ("Standard Upload", "/upload.html"),
    ("Enhanced Upload", "/upload-enhanced.html"),
    ("Enhanced Upload V2", "/upload-enhanced-v2.html"),
    ("Working Upload", "/upload-working.html"),
    ("AI Upload", "/upload-ai.html"),
]

working_uploads = []
for name, path in upload_pages:
    try:
        resp = requests.get(f"{PLATFORM_BASE}{path}", allow_redirects=False)
        if resp.status_code == 200:
            working_uploads.append((name, path))
            print(f"   {name}: ✓ Found")
        else:
            print(f"   {name}: ✗ ({resp.status_code})")
    except:
        print(f"   {name}: ✗ (Error)")

# 5. Test document operations
print("\n5. Testing Document Operations:")

# Get documents
resp = requests.get(f"{API_BASE}/api/user/intelligence-simple/documents/list", headers=headers)
if resp.status_code == 200:
    docs = resp.json().get("documents", [])
    print(f"   Documents found: {len(docs)}")
    
    if docs:
        # Test analyze on first doc
        doc_id = docs[0]["id"]
        print(f"   Testing analyze on document {doc_id}...")
        
        analyze_resp = requests.post(
            f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analyze",
            headers=headers,
            json={"documentId": doc_id}
        )
        print(f"   Analyze: {'✓' if analyze_resp.status_code == 200 else '✗'} ({analyze_resp.status_code})")
        
        if analyze_resp.status_code == 200:
            analysis = analyze_resp.json()
            if "analysis" in analysis and "mapped_standards" in analysis["analysis"]:
                print(f"   Standards mapped: {len(analysis['analysis']['mapped_standards'])}")

# 6. Summary and recommendations
print("\n" + "=" * 60)
print("\n📊 ANALYSIS SUMMARY:")

print("\n✅ Working Features:")
for name, result in api_results.items():
    if result["ok"]:
        print(f"   - {name}")

print(f"\n📄 Available Dashboards: {len(working_dashboards)}")
for name, path in working_dashboards[:3]:  # Show top 3
    print(f"   - {name}: {path}")

print(f"\n📤 Available Upload Pages: {len(working_uploads)}")
for name, path in working_uploads[:3]:  # Show top 3
    print(f"   - {name}: {path}")

print("\n🎯 RECOMMENDATION:")
if working_dashboards:
    # Check for A3E vs MapMyStandards branding
    has_enhanced = any("enhanced" in path.lower() for _, path in working_dashboards)
    has_modern = any("modern" in path.lower() for _, path in working_dashboards)
    
    if has_enhanced:
        print("   Use the Enhanced Dashboard (/dashboard-enhanced.html)")
        print("   - This appears to be the most complete version")
        print("   - Integrates with the user-intelligence-simple API")
    elif has_modern:
        print("   Use the Modern Dashboard (/dashboard-modern.html)")
        print("   - This is a newer, cleaner interface")
    else:
        print("   Use the standard Dashboard (/dashboard.html)")

print("\n⚠️  ISSUES TO ADDRESS:")
print("   - Multiple dashboard versions create confusion")
print("   - Upload functionality scattered across multiple pages")
print("   - Analysis results not persisting across pages")
print("   - Inconsistent branding (A3E vs MapMyStandards)")

print("\n💡 NEXT STEPS:")
print("   1. Consolidate to a single dashboard")
print("   2. Ensure analysis results persist in database")
print("   3. Create consistent navigation between pages")
print("   4. Standardize on either A3E or MapMyStandards branding")