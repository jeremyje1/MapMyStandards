#!/usr/bin/env python3
"""Test billing endpoints are accessible."""
import requests
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE = "https://api.mapmystandards.ai"
LOCAL_API_BASE = "http://localhost:8000"

# Choose which to test
USE_LOCAL = False  # Set to True to test local
BASE_URL = LOCAL_API_BASE if USE_LOCAL else API_BASE

# Test endpoints
endpoints = [
    ("GET", "/_sentinel_main", "Main sentinel check"),
    ("GET", "/api/v1/billing/single-plan-info", "Single plan info (v1)"),
    ("GET", "/api/billing/single-plan-info", "Single plan info (legacy)"),
    ("POST", "/api/v1/billing/create-single-plan-checkout", "Create checkout (v1)"),
    ("POST", "/api/billing/create-single-plan-checkout", "Create checkout (legacy)"),
]

def test_endpoint(method: str, path: str, description: str) -> Dict[str, Any]:
    """Test a single endpoint."""
    url = BASE_URL + path
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"URL: {method} {url}")
    
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            # POST with minimal payload
            payload = {
                "success_url": "https://platform.mapmystandards.ai/success",
                "cancel_url": "https://platform.mapmystandards.ai/cancel"
            }
            resp = requests.post(url, json=payload, timeout=10)
        
        print(f"Status: {resp.status_code}")
        
        # Try to parse response
        try:
            data = resp.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except:
            print(f"Response (text): {resp.text[:500]}")
        
        return {
            "success": resp.status_code < 500,
            "status": resp.status_code,
            "path": path
        }
        
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return {
            "success": False,
            "status": 0,
            "path": path,
            "error": str(e)
        }

def main():
    """Run all tests."""
    print(f"Testing API at: {BASE_URL}")
    print(f"Mode: {'LOCAL' if USE_LOCAL else 'PRODUCTION'}")
    
    results = []
    for method, path, description in endpoints:
        result = test_endpoint(method, path, description)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["success"])
    total = len(results)
    
    print(f"Successful: {success_count}/{total}")
    
    for r in results:
        status = "✓" if r["success"] else "✗"
        print(f"{status} {r['path']} - Status: {r['status']}")
    
    # Exit with error if any failed
    if success_count < total:
        sys.exit(1)

if __name__ == "__main__":
    main()
