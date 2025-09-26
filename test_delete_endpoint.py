#!/usr/bin/env python3
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Implc3RyZWxsYWtpc3MuaUBnbWFpbC5jb20iLCJzdWIiOiJqZXN0cmVsbGFraXNzLmlAZ21haWwuY29tIiwidXNlcl9pZCI6Implc3RyZWxsYWtpc3MuaUBnbWFpbC5jb20iLCJleHAiOjE3NjYxNjA1NDB9.uFJhBYJ8GJgdOovASxQfgr4LJtq7j9zx3g9mRhE0IjQ"

# Test a dummy doc ID to see if auth works
doc_id = "dummy-test-id"

url = f"https://api.mapmystandards.ai/api/user/intelligence-simple/documents/{doc_id}"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"Testing DELETE {url}")
print(f"Headers: {headers}")

try:
    response = requests.delete(url, headers=headers, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    print(response.text)
        
except Exception as e:
    print(f"Error: {e}")