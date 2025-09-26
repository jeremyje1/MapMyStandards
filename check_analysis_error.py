#!/usr/bin/env python3
"""Check what's happening with the analysis endpoint"""

import requests
import json

# Get a token first
login_url = "https://api.mapmystandards.ai/api/auth/login"
login_data = {
    "email": "jeremy.estrella@gmail.com",
    "password": "changeme123"
}

response = requests.post(login_url, json=login_data)
if response.status_code == 200:
    token = response.json()['access_token']
    print(f"Got token: {token[:20]}...")
else:
    print("Login failed:", response.text)
    exit(1)

# Test the analysis endpoint
doc_id = "4cc44ec8-1e58-4dca-81de-5e9537bb0765"
analysis_url = f"https://api.mapmystandards.ai/api/user/intelligence-simple/documents/{doc_id}/analysis"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"\nFetching analysis for document {doc_id}...")
response = requests.get(analysis_url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

# Also check if the document exists
docs_url = "https://api.mapmystandards.ai/api/user/intelligence-simple/uploads"
print(f"\nChecking if document exists in uploads...")
response = requests.get(docs_url, headers=headers)
if response.status_code == 200:
    docs = response.json()['documents']
    for doc in docs:
        if doc['id'] == doc_id:
            print(f"Found document: {doc}")
            break
    else:
        print(f"Document {doc_id} not found in uploads")