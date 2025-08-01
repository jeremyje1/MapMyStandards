#!/usr/bin/env python3
"""
Diagnostic startup script for Railway deployment
"""
import os
import sys
import time

print("🔍 Railway Deployment Diagnostics")
print("=" * 50)

# Check environment
print("\n📋 Environment Variables:")
print(f"   PORT: {os.getenv('PORT', 'Not set')}")
print(f"   PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
print(f"   PATH: {os.getenv('PATH', 'Not set')}")

# Check Python
print(f"\n🐍 Python Information:")
print(f"   Version: {sys.version}")
print(f"   Executable: {sys.executable}")

# Check working directory
print(f"\n📁 Working Directory:")
print(f"   Current: {os.getcwd()}")
print(f"   Contents: {os.listdir('.')}")

# Check if files exist
required_files = ['minimal_test_api.py', 'simple_trial_api_v2.py']
print(f"\n📄 Required Files:")
for file in required_files:
    exists = os.path.exists(file)
    print(f"   {file}: {'✅ Exists' if exists else '❌ Missing'}")

# Try importing dependencies
print(f"\n📦 Dependencies:")
try:
    import fastapi
    print(f"   fastapi: ✅ {fastapi.__version__}")
except ImportError as e:
    print(f"   fastapi: ❌ {e}")

try:
    import uvicorn
    print(f"   uvicorn: ✅ {uvicorn.__version__}")
except ImportError as e:
    print(f"   uvicorn: ❌ {e}")

# Test network binding
print(f"\n🌐 Network Test:")
try:
    import socket
    port = int(os.getenv('PORT', 8000))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.bind(('0.0.0.0', port))
    sock.close()
    print(f"   Port {port}: ✅ Available")
except Exception as e:
    print(f"   Port {port}: ❌ {e}")

print("\n" + "=" * 50)
print("🚀 Starting actual API...")

# Now start the actual API
try:
    from minimal_test_api import app
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    print(f"   Binding to 0.0.0.0:{port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="debug"
    )
except Exception as e:
    print(f"❌ Startup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
