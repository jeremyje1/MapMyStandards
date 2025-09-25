#!/usr/bin/env python3
"""Test the analyze and download endpoints that are failing in the frontend"""

import requests
import json

API_BASE = "https://api.mapmystandards.ai"

# Test token (you might need to update this with a valid token)
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqZXJlbXkuZXN0cmVsbGFAZ21haWwuY29tIiwiZXhwIjoxNzU5MDY4MDc0LCJpYXQiOjE3Mjc1MzIwNzQsInVzZXJfaWQiOiJqZXJlbXkuZXN0cmVsbGFAZ21haWwuY29tIiwiZW1haWwiOiJqZXJlbXkuZXN0cmVsbGFAZ21haWwuY29tIiwiZnVsbF9uYW1lIjoiSmVyZW15IEVzdHJlbGxhIn0.xvdULt_wNzCOcYZqBGJyv-OGD1hJezXQ0FU1c3bCKJY"

headers = {
    "Authorization": f"Bearer {TEST_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Test document ID from error
test_document_id = "9cdee4fa-74fd-4cb3-8e9a-ee32c33f3020"

print("Testing Analyze and Download Endpoints")
print("=" * 50)

# Test analyze endpoint
print(f"\n1. Testing analyze endpoint for document: {test_document_id}")
analyze_url = f"{API_BASE}/api/user/intelligence-simple/documents/{test_document_id}/analyze"
print(f"   URL: {analyze_url}")

try:
    response = requests.post(analyze_url, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    if response.status_code != 200:
        print(f"   Response: {response.text}")
    else:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test download endpoint
print(f"\n2. Testing download endpoint for document: {test_document_id}")
download_url = f"{API_BASE}/api/user/intelligence-simple/uploads/{test_document_id}"
print(f"   URL: {download_url}")

try:
    response = requests.get(download_url, headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    if response.status_code != 200:
        print(f"   Response: {response.text}")
    else:
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   Content-Length: {response.headers.get('content-length')}")
        print(f"   File downloaded successfully")
except Exception as e:
    print(f"   Error: {e}")

# Test if endpoints exist at all
print("\n3. Checking if endpoints are registered")
endpoints = [
    ("POST", "/api/user/intelligence-simple/documents/{id}/analyze"),
    ("GET", "/api/user/intelligence-simple/uploads/{id}"),
    ("GET", "/api/user/intelligence-simple/documents/list")
]

for method, path in endpoints:
    test_path = path.replace("{id}", "test-id")
    url = f"{API_BASE}{test_path}"
    print(f"\n   {method} {test_path}")
    try:
        if method == "POST":
            response = requests.post(url, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code in [401, 403]:
            print("   ✓ Endpoint exists (auth required)")
        elif response.status_code == 404:
            print("   ✗ Endpoint not found")
        elif response.status_code == 405:
            print("   ✗ Method not allowed")
        elif response.status_code == 422:
            print("   ✓ Endpoint exists (validation error)")
        elif response.status_code >= 500:
            print("   ! Server error")
    except Exception as e:
        print(f"   Error: {e}")