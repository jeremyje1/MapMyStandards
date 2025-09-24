#!/usr/bin/env python3
"""Test complete upload functionality with S3 integration."""

import requests
import json
import sys
import time
from pathlib import Path

API_URL = "https://api.mapmystandards.ai/api"

def test_upload_with_s3():
    """Test document upload with S3 integration."""
    print("\n=== Testing Complete Upload with S3 ===")
    
    # Get token for jeremy@mapmystandards.com
    print("\n1. Getting auth token...")
    auth_response = requests.post(
        f"{API_URL}/auth/login",
        json={
            "email": "jeremy@mapmystandards.com",
            "password": "Test123!@#"
        }
    )
    
    if auth_response.status_code == 200:
        token = auth_response.json().get("access_token")
        print("✓ Auth successful")
    else:
        print(f"✗ Auth failed: {auth_response.status_code} - {auth_response.text}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test file
    print("\n2. Creating test file...")
    test_content = b"This is a test document for S3 upload testing.\n" * 100
    test_file = ("test_document.pdf", test_content, "application/pdf")
    
    # Test upload endpoint
    print("\n3. Testing document upload...")
    files = {"file": test_file}
    data = {"category": "policies"}
    
    upload_response = requests.post(
        f"{API_URL}/documents/upload",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Upload response status: {upload_response.status_code}")
    if upload_response.status_code == 200:
        result = upload_response.json()
        print("✓ Upload successful!")
        print(f"  Document ID: {result.get('document_id')}")
        print(f"  S3 Key: {result.get('s3_key')}")
        print(f"  Status: {result.get('status')}")
        document_id = result.get('document_id')
    else:
        print(f"✗ Upload failed: {upload_response.text}")
        return
    
    # Test list documents
    print("\n4. Testing document list...")
    list_response = requests.get(
        f"{API_URL}/documents",
        headers=headers
    )
    
    print(f"List response status: {list_response.status_code}")
    if list_response.status_code == 200:
        documents = list_response.json().get("documents", [])
        print(f"✓ Found {len(documents)} documents")
        for doc in documents[:5]:  # Show first 5
            print(f"  - {doc.get('original_name')} ({doc.get('category')})")
    else:
        print(f"✗ List failed: {list_response.text}")
    
    # Test download
    if document_id:
        print(f"\n5. Testing document download (ID: {document_id})...")
        download_response = requests.get(
            f"{API_URL}/documents/{document_id}/download",
            headers=headers
        )
        
        print(f"Download response status: {download_response.status_code}")
        if download_response.status_code == 200:
            data = download_response.json()
            if data.get("download_url"):
                print("✓ Got download URL")
                print(f"  URL: {data['download_url'][:50]}...")
            else:
                print("✓ Got file content")
                print(f"  Size: {len(download_response.content)} bytes")
        else:
            print(f"✗ Download failed: {download_response.text}")
    
    # Test notifications
    print("\n6. Testing notifications endpoint...")
    notif_response = requests.get(
        f"{API_URL}/documents/notifications",
        headers=headers
    )
    
    print(f"Notifications response status: {notif_response.status_code}")
    if notif_response.status_code == 200:
        notifications = notif_response.json().get("notifications", [])
        print(f"✓ Found {len(notifications)} notifications")
    else:
        print(f"✗ Notifications failed: {notif_response.text}")
    
    # Test delete
    if document_id:
        print(f"\n7. Testing document delete (ID: {document_id})...")
        delete_response = requests.delete(
            f"{API_URL}/documents/{document_id}",
            headers=headers
        )
        
        print(f"Delete response status: {delete_response.status_code}")
        if delete_response.status_code == 200:
            print("✓ Document deleted successfully")
        else:
            print(f"✗ Delete failed: {delete_response.text}")
    
    print("\n=== Upload Test Complete ===")

if __name__ == "__main__":
    test_upload_with_s3()
