#!/usr/bin/env python3
"""Test the debug endpoint to see what's happening"""

import requests

# Test document
doc_id = "48e43e1e-559a-44d0-9ddd-0b18258d125a"
api_url = "https://api.mapmystandards.ai"

# Test without auth first
print("Testing debug endpoint without auth...")
response = requests.get(f"{api_url}/api/user/intelligence-simple/debug/analysis/{doc_id}")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Test the regular analysis endpoint to see the error
print("\nTesting regular analysis endpoint without auth...")
response = requests.get(f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis")
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500]}")