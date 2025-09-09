#!/usr/bin/env python3
"""
Server-side S3 upload test (no CORS issues)
Tests the upload functionality directly from Python
"""

import requests
import os
import sys
from pathlib import Path

API_URL = "https://api.mapmystandards.ai"

def test_health():
    """Test API health"""
    print("📡 Testing API health...")
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API is {data['status']}")
        print(f"   Environment: {data['environment']}")
        return True
    else:
        print(f"❌ API health check failed: {response.status_code}")
        return False

def test_login(email, password):
    """Test login"""
    print("\n🔐 Testing login...")
    
    # Try simple auth first
    response = requests.post(
        f"{API_URL}/auth-simple/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code != 200:
        # Try regular auth
        response = requests.post(
            f"{API_URL}/auth/login",
            json={
                "email": email,
                "password": password,
                "first_name": "Test",
                "last_name": "User"
            }
        )
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('token') or data.get('access_token') or data.get('api_key')
        print(f"✅ Login successful!")
        print(f"   Token received: {'Yes' if token else 'No'}")
        return token
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None

def test_upload_presign(token):
    """Test presigned URL generation"""
    print("\n📤 Testing S3 presigned URL generation...")
    
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    response = requests.post(
        f"{API_URL}/upload/presign",
        json={
            "filename": "test-file.txt",
            "content_type": "text/plain",
            "file_size": 100
        },
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Presigned URL generated!")
        print(f"   Upload URL: {data['upload_url']}")
        print(f"   File key: {data['file_key']}")
        return data
    else:
        print(f"❌ Presigned URL generation failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
        # Try the existing upload endpoint
        print("\n📤 Trying existing /api/documents/upload endpoint...")
        
        # Create a test file
        test_file_path = "test_upload.txt"
        with open(test_file_path, "w") as f:
            f.write("This is a test file for S3 upload")
        
        with open(test_file_path, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            headers = {"Authorization": f"Bearer {token}"} if token else {}
            
            response = requests.post(
                f"{API_URL}/api/documents/upload",
                files=files,
                headers=headers
            )
            
        os.remove(test_file_path)
        
        if response.status_code == 200:
            print(f"✅ File uploaded using existing endpoint!")
            return response.json()
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        
        return None

def main():
    print("="*60)
    print("🧪 MapMyStandards S3 Upload Test (Server-side)")
    print("="*60)
    
    # Test health
    if not test_health():
        print("\n⚠️  API might be down or deploying")
        return
    
    # Get credentials
    email = input("\nEnter your email (or press Enter for jeremy@northpathstrategies.org): ").strip()
    if not email:
        email = "jeremy@northpathstrategies.org"
    
    password = input("Enter your password: ").strip()
    if not password:
        print("❌ Password is required")
        return
    
    # Test login
    token = test_login(email, password)
    
    if token:
        # Test upload
        test_upload_presign(token)
    
    print("\n" + "="*60)
    print("Test complete!")
    print("="*60)

if __name__ == "__main__":
    main()