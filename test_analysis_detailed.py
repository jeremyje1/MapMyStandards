#!/usr/bin/env python3
"""Test the analysis endpoint with detailed error checking"""

import requests
import json

# Test document
doc_id = "2e6f4c4c-1d80-452e-b4e0-299f3d192b73"
api_url = "https://api.mapmystandards.ai"

print("Testing analysis endpoint...")

# First, test without auth to see the raw error
response = requests.get(
    f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
    headers={
        "Content-Type": "application/json"
    }
)

print(f"Without auth - Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Test with a dummy token to see if we get a different error
response = requests.get(
    f"{api_url}/api/user/intelligence-simple/documents/{doc_id}/analysis",
    headers={
        "Authorization": "Bearer dummy-token",
        "Content-Type": "application/json"
    }
)

print(f"\nWith dummy auth - Status: {response.status_code}")
print(f"Response: {response.text[:500]}")

# Check the health endpoint
response = requests.get(f"{api_url}/health")
print(f"\nHealth check - Status: {response.status_code}")
print(f"Response: {response.text}")