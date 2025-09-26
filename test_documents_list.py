#!/usr/bin/env python3
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6Implc3RyZWxsYWtpc3MuaUBnbWFpbC5jb20iLCJzdWIiOiJqZXN0cmVsbGFraXNzLmlAZ21haWwuY29tIiwidXNlcl9pZCI6Implc3RyZWxsYWtpc3MuaUBnbWFpbC5jb20iLCJleHAiOjE3NjYxNjA1NDB9.uFJhBYJ8GJgdOovASxQfgr4LJtq7j9zx3g9mRhE0IjQ"

url = "https://api.mapmystandards.ai/api/user/intelligence-simple/documents/list"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print(f"Testing {url}")
print(f"Headers: {headers}")

try:
    response = requests.get(url, headers=headers, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nResponse:")
    
    if response.status_code == 200:
        import json
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")