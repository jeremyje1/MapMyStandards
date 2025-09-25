#!/usr/bin/env python3
"""Test with the actual token"""

import requests
import json
import base64

API_BASE = "https://api.mapmystandards.ai"

# The token from the login
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlMTQ0Y2Y5MC1kOGVkLTQyNzctYmYxMi0zZDg2NDQzZTIwOTkiLCJlbWFpbCI6ImplcmVteS5lc3RyZWxsYUBnbWFpbC5jb20iLCJleHAiOjE3NTg4MjQ4NTcsImlhdCI6MTc1ODgyMzA1N30.091bNse5RCxoeBpZOXdyO8HIomoJpLTSDMov_qlsDVA"

print("=" * 60)
print("Testing with Jeremy's token")
print("=" * 60)

# Decode token first
parts = TOKEN.split('.')
if len(parts) == 3:
    payload = base64.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4))
    payload_dict = json.loads(payload)
    print("\nToken payload:")
    print(json.dumps(payload_dict, indent=2))
    
    # Check format
    sub = payload_dict.get('sub', '')
    if '@' in sub:
        print("\n⚠️  Token has email in 'sub' field (old format)")
    else:
        print("\n✓ Token has UUID in 'sub' field (correct format)")
        print(f"  UUID: {sub}")

# Set up headers
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Test documents list
print("\n1. Testing documents list...")
response = requests.get(f"{API_BASE}/api/user/intelligence-simple/documents/list", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    docs_data = response.json()
    documents = docs_data.get("documents", [])
    print(f"   ✓ Found {len(documents)} documents")
    
    # Show first few documents
    for i, doc in enumerate(documents[:5]):
        print(f"\n   Document {i+1}:")
        print(f"   - ID: {doc.get('id')}")
        print(f"   - Title: {doc.get('title', 'N/A')[:50]}...")
        print(f"   - Upload ID: {doc.get('upload_id')}")
        print(f"   - User ID: {doc.get('user_id', 'N/A')}")
else:
    print(f"   ✗ Error: {response.text}")

# Test specific document
doc_id = "440cc1fa-2d43-4b6a-b238-fd2a13025c9f"
print(f"\n2. Testing analyze for document {doc_id}...")
analyze_data = {"documentId": doc_id}
response = requests.post(
    f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analyze", 
    headers=headers,
    json=analyze_data
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Analyze working!")
    result = response.json()
    print(f"   Analysis type: {result.get('analysis', {}).get('type', 'N/A')}")
else:
    print(f"   ✗ Error: {response.text[:500]}")

# Test download
print(f"\n3. Testing download for document {doc_id}...")
response = requests.get(
    f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/download", 
    headers=headers
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Download working!")
    print(f"   Content-Type: {response.headers.get('Content-Type')}")
    print(f"   Content-Length: {len(response.content)} bytes")
else:
    print(f"   ✗ Error: {response.text[:500]}")

# Test dashboard metrics
print(f"\n4. Testing dashboard metrics...")
response = requests.get(f"{API_BASE}/api/user/intelligence-simple/dashboard/metrics", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   ✓ Dashboard metrics working!")
    metrics = response.json()
    print(f"   Total documents: {metrics.get('total_documents', 0)}")
    print(f"   Total uploads: {metrics.get('total_uploads', 0)}")
else:
    print(f"   ✗ Error: {response.text[:500]}")

print("\n" + "=" * 60)