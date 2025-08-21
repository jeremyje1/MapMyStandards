#!/usr/bin/env python3
"""Monitor for FastAPI deployment"""

import time
import subprocess
import json

print("🔄 Monitoring for FastAPI deployment...")
print("Looking for the new health endpoint format...")

start_time = time.time()
max_wait = 300  # 5 minutes

while time.time() - start_time < max_wait:
    try:
        # Use curl to get the health endpoint
        result = subprocess.run(
            ["curl", "-s", "https://mapmystandards-prod-production.up.railway.app/health"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                
                # Check if it's the FastAPI response (has more fields)
                if "status" in data and "service" in data:
                    if "database" in data or "version" in data or len(data) > 3:
                        print(f"\n✅ FastAPI is now running!")
                        print(f"Response: {json.dumps(data, indent=2)}")
                        print(f"\nTotal wait time: {int(time.time() - start_time)} seconds")
                        
                        # Test API endpoints
                        print("\nTesting API endpoints...")
                        endpoints = [
                            ("GET", "/docs"),
                            ("GET", "/api/trial/signup"),  # Should return 405 for GET
                            ("POST", "/api/trial/signup"),  # Test with empty data
                        ]
                        
                        for method, endpoint in endpoints:
                            if method == "GET":
                                cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", 
                                      f"https://mapmystandards-prod-production.up.railway.app{endpoint}"]
                            else:
                                cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                                      "-X", method, "-H", "Content-Type: application/json",
                                      "-d", "{}", 
                                      f"https://mapmystandards-prod-production.up.railway.app{endpoint}"]
                            
                            status = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
                            print(f"   {method} {endpoint}: {status}")
                        
                        break
                    else:
                        # Still the old Flask app
                        elapsed = int(time.time() - start_time)
                        print(f"\r⏳ Still Flask app... ({elapsed}s) - {data.get('service', 'unknown')}", end="", flush=True)
                        
            except json.JSONDecodeError:
                pass
                
    except Exception as e:
        pass
    
    time.sleep(5)

if time.time() - start_time >= max_wait:
    print("\n\n❌ Timeout waiting for FastAPI deployment.")
    print("The Flask app is still responding. Check Railway dashboard for deployment status.")
