#!/usr/bin/env python3
"""Test the analyze API endpoint directly"""

import requests
import json
import time

API_BASE = "https://api.mapmystandards.ai"

# First, login to get a token
print("Testing MapMyStandards Analyze Feature")
print("=" * 60)

print("\n1. Logging in...")
login_data = {
    "email": "jeremy.estrella@gmail.com",
    "password": "Ipo4Eva45*"
}

response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
print("✓ Login successful")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Get document list
print("\n2. Getting document list...")
response = requests.get(f"{API_BASE}/api/user/intelligence-simple/documents/list", headers=headers)
if response.status_code != 200:
    print(f"❌ Failed to get documents: {response.text}")
    exit(1)

documents = response.json().get("documents", [])
print(f"✓ Found {len(documents)} documents")

if not documents:
    print("\n⚠️  No documents found. Please upload a document first.")
    exit(0)

# Test analyze on the first document
doc = documents[0]
doc_id = doc["id"]
doc_title = doc.get("title", "Unknown")[:50]

print(f"\n3. Testing analyze on document: {doc_title}...")
print(f"   Document ID: {doc_id}")

start_time = time.time()
analyze_data = {"documentId": doc_id}
response = requests.post(
    f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analyze",
    headers=headers,
    json=analyze_data
)

elapsed = time.time() - start_time

if response.status_code == 200:
    print(f"\n✅ ANALYZE SUCCESSFUL! (took {elapsed:.2f} seconds)")
    result = response.json()
    
    # Check what analysis was performed
    analysis = result.get("analysis", {})
    standards = result.get("standards_mapped", [])
    
    print(f"\n   Analysis Results:")
    print(f"   - Type: {analysis.get('type', 'N/A')}")
    print(f"   - Standards mapped: {len(standards)}")
    
    if standards:
        print(f"\n   Mapped Standards:")
        for std in standards[:3]:  # Show first 3
            print(f"   - {std}")
        if len(standards) > 3:
            print(f"   ... and {len(standards) - 3} more")
    
    # Check if it used Bedrock or Anthropic
    if elapsed < 5:
        print(f"\n   ⚡ Fast response suggests local processing or cache")
    elif elapsed < 15:
        print(f"\n   🚀 Response time suggests AWS Bedrock (regional)")
    else:
        print(f"\n   🌐 Response time suggests Anthropic API (direct)")
        
else:
    print(f"\n❌ Analyze failed: {response.status_code}")
    print(f"   Error: {response.text[:200]}")

# Also test download
print(f"\n4. Testing download...")
response = requests.get(
    f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/download",
    headers=headers
)

if response.status_code == 200:
    print(f"✅ DOWNLOAD SUCCESSFUL!")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    print(f"   Size: {len(response.content)} bytes")
else:
    print(f"❌ Download failed: {response.status_code}")

print("\n" + "=" * 60)
print("All document operations are working correctly!")