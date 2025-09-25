#!/usr/bin/env python3
"""Debug download issues"""

import requests
import json

API_BASE = "https://api.mapmystandards.ai"

print("🔍 Debug Download Test")
print("=" * 60)

# 1. Login
print("\n1. Logging in...")
response = requests.post(f"{API_BASE}/api/auth/login", json={
    "email": "jeremy.estrella@gmail.com",
    "password": "Ipo4Eva45*"
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    exit(1)

token = response.json()["access_token"]
print(f"✓ Login successful")
print(f"Token (first 20 chars): {token[:20]}...")

# 2. Get user info and documents
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{API_BASE}/api/user/intelligence-simple/documents/list", headers=headers)
data = response.json()

print(f"\n2. Documents response:")
print(f"   Status: {response.status_code}")
print(f"   User ID: {data.get('user_id', 'N/A')}")
print(f"   Document count: {len(data.get('documents', []))}")

if data.get("documents"):
    doc = data["documents"][0]
    doc_id = doc["id"]
    user_id = data.get("user_id")
    
    print(f"\n3. First document details:")
    print(f"   ID: {doc_id}")
    print(f"   Title: {doc.get('title', 'N/A')}")
    print(f"   Filename: {doc.get('filename', 'N/A')}")
    print(f"   User ID: {doc.get('user_id', 'N/A')}")
    print(f"   File Key: {doc.get('file_key', 'N/A')[:50]}...")
    
    # Test download with debug
    print(f"\n4. Testing download endpoint...")
    download_url = f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/download"
    print(f"   URL: {download_url}")
    
    response = requests.get(download_url, headers=headers)
    print(f"   Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"   Response headers: {dict(response.headers)}")
        print(f"   Response body: {response.text[:500]}")
    else:
        print(f"   ✅ Download successful!")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
        print(f"   Content-Length: {len(response.content)} bytes")

print("\n" + "=" * 60)