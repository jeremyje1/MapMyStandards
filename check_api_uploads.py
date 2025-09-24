#!/usr/bin/env python3
"""
Check uploads via the API to diagnose the issue
"""

import requests
import json
import sys

# API Configuration
API_BASE = "https://api.mapmystandards.ai"

def check_api_uploads(token):
    """Check uploads via the API"""
    
    print("\n=== Checking Uploads via API ===\n")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Check uploads endpoint
    try:
        response = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/uploads",
            headers=headers
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nResponse: {json.dumps(data, indent=2)}")
            
            # Display evidence/documents
            evidence = data.get("evidence", data.get("documents", []))
            print(f"\n✅ Total Documents Found: {len(evidence)}")
            
            if evidence:
                print("\nDocument Details:")
                for idx, doc in enumerate(evidence, 1):
                    print(f"\n{idx}. {doc.get('filename', 'Unknown')}")
                    print(f"   - Uploaded: {doc.get('uploaded_at', 'Unknown')}")
                    print(f"   - Size: {doc.get('size', 0)} bytes")
                    print(f"   - ID: {doc.get('id', 'No ID')}")
                    print(f"   - Path: {doc.get('saved_path', 'No path')}")
            else:
                print("\n❌ No documents found in the response")
                print("\nPossible reasons:")
                print("1. The backend hasn't been deployed with database changes yet")
                print("2. Uploads are being saved to JSON file that gets wiped on deploy")
                print("3. The token/user mismatch")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking uploads: {e}")


def main():
    # Get token from localStorage on the platform
    print("To get your token:")
    print("1. Go to https://platform.mapmystandards.ai")
    print("2. Open browser DevTools (F12)")
    print("3. Go to Console tab")
    print("4. Type: localStorage.getItem('access_token')")
    print("5. Copy the token (without quotes)")
    print()
    
    token = input("Enter your access token: ").strip()
    
    if not token:
        print("❌ No token provided")
        sys.exit(1)
        
    check_api_uploads(token)


if __name__ == "__main__":
    main()