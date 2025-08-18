#!/usr/bin/env python3
"""
Test script to mimic Railway's health check behavior
"""

import requests
import time
import sys

def test_health_check(base_url, max_attempts=15):
    """Test health check like Railway does"""
    
    print(f"🔍 Testing health check for: {base_url}")
    print("=" * 50)
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt #{attempt}...")
            
            # Test root endpoint
            print("  Testing root endpoint...")
            response = requests.get(f"{base_url}/", timeout=10)
            print(f"  Root status: {response.status_code}")
            
            # Test health endpoint
            print("  Testing health endpoint...")
            health_response = requests.get(f"{base_url}/health", timeout=10)
            print(f"  Health status: {health_response.status_code}")
            
            if health_response.status_code == 200:
                print("✅ SUCCESS: Health check passed!")
                print(f"   Response: {health_response.json()}")
                return True
            else:
                print(f"❌ Health check failed with status: {health_response.status_code}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection failed: {e}")
        except requests.exceptions.Timeout as e:
            print(f"❌ Request timed out: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        
        if attempt < max_attempts:
            print("   Waiting 10 seconds before retry...")
            time.sleep(10)
    
    print("\n❌ All attempts failed!")
    return False

if __name__ == "__main__":
    # Test with the Railway URL when available
    # For now, test local if available
    
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "http://localhost:8080"
    
    print("🏥 Railway Health Check Simulator")
    print("=" * 50)
    
    success = test_health_check(url)
    
    if success:
        print("\n🎉 Health check simulation PASSED!")
    else:
        print("\n💔 Health check simulation FAILED!")
