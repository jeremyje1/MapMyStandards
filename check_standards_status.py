#!/usr/bin/env python3
"""Check standards corpus status in production"""
import requests
import json
import sys
import time
from datetime import datetime

def check_standards_status():
    """Check the production standards corpus status"""
    base_url = "https://api.mapmystandards.ai"
    
    # Try to get corpus status without auth first (public endpoint)
    print("🔍 Checking standards corpus status...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    endpoints = [
        "/api/user/intelligence-simple/standards/list?limit=5",
        "/api/user/intelligence-simple/standards/corpus/status",
        "/api/user/intelligence-simple/standards/metadata"
    ]
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"\n📡 Checking: {endpoint}")
            
            # Try without auth first
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if "standards" in endpoint:
                    if isinstance(data, dict):
                        if "standards" in data:
                            standards = data["standards"]
                            print(f"✅ Found {len(standards)} standards")
                            for std in standards[:3]:  # Show first 3
                                print(f"   - {std.get('id', 'Unknown')}: {std.get('title', 'Unknown')}")
                            if len(standards) > 3:
                                print(f"   ... and {len(standards) - 3} more")
                        elif "corpus_status" in data:
                            status = data.get("corpus_status", {})
                            print(f"📊 Corpus Status:")
                            for key, value in status.items():
                                print(f"   - {key}: {value}")
                        else:
                            print(f"📋 Response: {json.dumps(data, indent=2)}")
                    else:
                        print(f"📋 Response: {data}")
            else:
                print(f"❌ Status: {response.status_code}")
                if response.status_code == 401:
                    print("   (Authentication required)")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {str(e)}")
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
    
    print("\n" + "-" * 50)
    print("💡 Tip: If standards are limited, the deployment may still be in progress.")
    print("   Railway usually takes 2-5 minutes to deploy after pushing to GitHub.")
    print("   Run this script again in a few minutes to check if standards are loaded.")

def wait_for_deployment(max_wait_minutes=10):
    """Wait for deployment to complete and standards to load"""
    print(f"\n⏳ Monitoring deployment for up to {max_wait_minutes} minutes...")
    
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    check_interval = 30  # Check every 30 seconds
    
    while (time.time() - start_time) < max_wait_seconds:
        check_standards_status()
        
        # Check if we have more than seed standards (> 10)
        try:
            response = requests.get(
                "https://api.mapmystandards.ai/api/user/intelligence-simple/standards/list?limit=100",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "standards" in data:
                    num_standards = len(data["standards"])
                    if num_standards > 10:
                        print(f"\n🎉 Success! Found {num_standards} standards loaded!")
                        return True
        except:
            pass
        
        elapsed = int(time.time() - start_time)
        remaining = max_wait_seconds - elapsed
        if remaining > 0:
            print(f"\n⏱️  Waiting {check_interval}s before next check... ({remaining}s remaining)")
            time.sleep(check_interval)
    
    print(f"\n⏱️  Timeout after {max_wait_minutes} minutes. Standards may still be loading.")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--wait":
        wait_for_deployment()
    else:
        check_standards_status()
