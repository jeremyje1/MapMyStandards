#!/usr/bin/env python3
"""
Check upload persistence and storage
"""

import os
import json
import requests
from datetime import datetime

# Check if uploads are being persisted
UPLOADS_STORE = os.getenv("USER_UPLOADS_STORE", "user_uploads_store.json")

print("=== Checking Upload Persistence ===\n")

# Check if uploads store file exists
if os.path.exists(UPLOADS_STORE):
    print(f"✅ Uploads store file exists: {UPLOADS_STORE}")
    
    # Load and display contents
    try:
        with open(UPLOADS_STORE, 'r') as f:
            data = json.load(f)
        
        print(f"\nTotal users with uploads: {len(data)}")
        
        for user_key, user_data in data.items():
            docs = user_data.get("documents", [])
            if docs:
                print(f"\nUser: {user_key}")
                print(f"  Documents: {len(docs)}")
                for doc in docs[-5:]:  # Show last 5 documents
                    print(f"  - {doc.get('filename', 'Unknown')}")
                    print(f"    Size: {doc.get('size', 0)} bytes")
                    print(f"    Uploaded: {doc.get('uploaded_at', 'Unknown')}")
                    print(f"    Path: {doc.get('saved_path', 'No path')}")
                    
    except Exception as e:
        print(f"❌ Error reading uploads store: {e}")
else:
    print(f"❌ Uploads store file not found: {UPLOADS_STORE}")
    print("   This might be why uploads aren't persisting!")

# Check environment variables
print("\n\n=== Environment Variables ===\n")

storage_vars = [
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY", 
    "AWS_REGION",
    "S3_BUCKET_NAME",
    "S3_BUCKET",
    "MMS_ARTIFACTS_BUCKET",
    "USER_UPLOADS_STORE",
    "DATABASE_URL",
    "DB_CONNECTION_STRING"
]

for var in storage_vars:
    value = os.getenv(var)
    if value:
        if "KEY" in var or "SECRET" in var or "PASSWORD" in var:
            print(f"✅ {var}: ***hidden***")
        else:
            print(f"✅ {var}: {value[:50]}...")
    else:
        print(f"❌ {var}: Not set")

# Check if we can connect to the API
print("\n\n=== API Connection Test ===\n")

try:
    response = requests.get("https://api.mapmystandards.ai/health")
    if response.status_code == 200:
        print("✅ API is reachable")
    else:
        print(f"⚠️ API returned status: {response.status_code}")
except Exception as e:
    print(f"❌ Cannot reach API: {e}")
