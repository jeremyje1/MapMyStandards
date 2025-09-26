#!/usr/bin/env python3
"""Test the full analysis flow to debug the 500 error"""

import requests
import json
import time

# API configuration
api_url = "https://api.mapmystandards.ai"
email = "test@example.com"
password = "testpassword123"

# Step 1: Try to login
print("1. Attempting login...")
login_response = requests.post(
    f"{api_url}/api/auth/login",
    json={"email": email, "password": password}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.status_code}")
    print(f"Response: {login_response.text}")
    # Try with a different endpoint
    print("\nTrying alternative login endpoint...")
    login_response = requests.post(
        f"{api_url}/auth/login",
        json={"email": email, "password": password}
    )
    if login_response.status_code != 200:
        print(f"Alternative login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        exit(1)

token = login_response.json().get('access_token')
print(f"Login successful! Token: {token[:20]}...")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Step 2: Check what documents exist
print("\n2. Checking existing documents...")
docs_response = requests.get(
    f"{api_url}/api/user/intelligence-simple/uploads",
    headers=headers
)

if docs_response.status_code == 200:
    docs = docs_response.json().get('documents', [])
    print(f"Found {len(docs)} documents")
    if docs:
        # Try to get analysis for the first document
        doc_id = docs[0]['id']
        print(f"\n3. Testing analysis for document: {doc_id}")
        
        analysis_response = requests.get(
            f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
            headers=headers
        )
        
        print(f"Analysis status: {analysis_response.status_code}")
        print(f"Response: {analysis_response.text[:1000]}")
else:
    print(f"Failed to get documents: {docs_response.status_code}")
    print(f"Response: {docs_response.text}")

# Step 3: Test with the specific document ID from the error
print("\n4. Testing specific document from error...")
doc_id = "48e43e1e-559a-44d0-9ddd-0b18258d125a"
analysis_response = requests.get(
    f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
    headers=headers
)

print(f"Status: {analysis_response.status_code}")
print(f"Response: {analysis_response.text[:1000]}")

# Step 4: Check if it's a CORS issue by testing preflight
print("\n5. Testing CORS preflight...")
preflight_response = requests.options(
    f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
    headers={
        "Origin": "https://platform.mapmystandards.ai",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type"
    }
)
print(f"Preflight status: {preflight_response.status_code}")
print(f"CORS headers: {dict(preflight_response.headers)}")