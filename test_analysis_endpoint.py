#!/usr/bin/env python3
"""Test the analysis endpoint"""

import requests

# Test OPTIONS preflight request
api_url = "https://api.mapmystandards.ai"
doc_id = "52eb83d4-a071-43af-ace1-576dcea2bf98"

print("Testing OPTIONS preflight request...")
response = requests.options(
    f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
    headers={
        "Origin": "https://platform.mapmystandards.ai",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization,content-type"
    }
)
print(f"OPTIONS Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")

# Test GET request
print("\nTesting GET request...")
response = requests.get(
    f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
    headers={
        "Origin": "https://platform.mapmystandards.ai"
    }
)
print(f"GET Status: {response.status_code}")
if response.status_code != 200:
    print(f"Response: {response.text}")