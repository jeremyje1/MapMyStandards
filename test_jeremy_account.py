#!/usr/bin/env python3
"""Test Jeremy's account functionality"""

import requests
import json
import time

API_BASE = "https://api.mapmystandards.ai"
FRONTEND_BASE = "https://platform.mapmystandards.ai"

# Test credentials
EMAIL = "jeremy.estrella@gmail.com"
PASSWORD = "Ipo4Eva45*"

print("=" * 60)
print("Testing Jeremy's MapMyStandards Account")
print("=" * 60)

# Step 1: Login
print("\n1. Testing login...")
login_data = {
    "email": EMAIL,
    "password": PASSWORD,
    "remember": True
}

try:
    response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
    print(f"   Login status: {response.status_code}")
    
    if response.status_code == 200:
        login_response = response.json()
        token = login_response.get("token")
        user_info = login_response.get("user", {})
        print(f"   ✓ Login successful!")
        print(f"   User ID: {user_info.get('user_id', 'N/A')}")
        print(f"   Email: {user_info.get('email', 'N/A')}")
        print(f"   Name: {user_info.get('name', 'N/A')}")
        
        # Decode token to check format
        if token:
            import base64
            parts = token.split('.')
            if len(parts) == 3:
                payload = base64.urlsafe_b64decode(parts[1] + '=' * (4 - len(parts[1]) % 4))
                payload_dict = json.loads(payload)
                print(f"\n   Token payload:")
                print(f"   - sub: {payload_dict.get('sub', 'N/A')}")
                print(f"   - user_id: {payload_dict.get('user_id', 'N/A')}")
                print(f"   - email: {payload_dict.get('email', 'N/A')}")
                
                # Check if sub contains UUID or email
                sub = payload_dict.get('sub', '')
                if '@' in sub:
                    print(f"   ⚠️  WARNING: Token has email in 'sub' field (old format)")
                else:
                    print(f"   ✓ Token has UUID in 'sub' field (correct format)")
        
        # Step 2: Test authenticated endpoints
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Test documents list
        print("\n2. Testing documents list...")
        response = requests.get(f"{API_BASE}/api/user/intelligence-simple/documents/list", headers=headers)
        print(f"   Documents list status: {response.status_code}")
        if response.status_code == 200:
            docs_data = response.json()
            documents = docs_data.get("documents", [])
            print(f"   ✓ Found {len(documents)} documents")
            
            # Show first few documents
            for i, doc in enumerate(documents[:3]):
                print(f"\n   Document {i+1}:")
                print(f"   - ID: {doc.get('id', 'N/A')}")
                print(f"   - Title: {doc.get('title', 'N/A')}")
                print(f"   - Upload ID: {doc.get('upload_id', 'N/A')}")
        else:
            print(f"   ✗ Error: {response.text[:200]}")
        
        # Test specific document if ID provided
        doc_id = "440cc1fa-2d43-4b6a-b238-fd2a13025c9f"
        print(f"\n3. Testing analyze for document {doc_id}...")
        analyze_data = {"documentId": doc_id}
        response = requests.post(
            f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analyze", 
            headers=headers,
            json=analyze_data
        )
        print(f"   Analyze status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Analyze endpoint working!")
        else:
            print(f"   ✗ Error: {response.text[:200]}")
        
        # Test download
        print(f"\n4. Testing download for document {doc_id}...")
        response = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/download", 
            headers=headers
        )
        print(f"   Download status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Download endpoint working!")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"   Content-Length: {len(response.content)} bytes")
        else:
            print(f"   ✗ Error: {response.text[:200]}")
        
        # Test dashboard metrics
        print(f"\n5. Testing dashboard metrics...")
        response = requests.get(f"{API_BASE}/api/user/intelligence-simple/dashboard/metrics", headers=headers)
        print(f"   Dashboard metrics status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✓ Dashboard metrics working!")
        else:
            print(f"   ✗ Error: {response.text[:200]}")
            
    else:
        print(f"   ✗ Login failed!")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"   ✗ Error during testing: {e}")

print("\n" + "=" * 60)
print("Test complete!")
print("\nIf analyze/download are still failing with 500/404 errors,")
print("the issue may be with document ownership or database queries.")