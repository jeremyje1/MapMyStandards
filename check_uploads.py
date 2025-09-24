#!/usr/bin/env python3
"""
Check user uploads via the API
"""

import requests
import json
import sys

# API Configuration
API_BASE = "https://api.mapmystandards.ai"

def check_uploads(token):
    """Check user uploads via the API"""
    
    print("\n=== Checking User Uploads ===\n")
    
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
            print(f"\nTotal Documents: {len(evidence)}")
            
            if evidence:
                print("\nDocument Details:")
                for idx, doc in enumerate(evidence, 1):
                    print(f"\n{idx}. {doc.get('filename', 'Unknown')}")
                    print(f"   - Uploaded: {doc.get('uploaded_at', 'Unknown')}")
                    print(f"   - Status: {doc.get('status', 'Unknown')}")
                    print(f"   - Standards Mapped: {len(doc.get('standards_mapped', []))}")
                    print(f"   - Saved Path: {doc.get('saved_path', 'Not specified')}")
                    print(f"   - Fingerprint: {doc.get('fingerprint', 'Not specified')}")
            else:
                print("\nNo documents found.")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error checking uploads: {e}")


def main():
    # Get token from command line or use test token
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        # Try to use a test token or prompt user
        token = input("Enter your access token: ").strip()
    
    if not token:
        print("Error: No token provided")
        sys.exit(1)
        
    check_uploads(token)


if __name__ == "__main__":
    main()