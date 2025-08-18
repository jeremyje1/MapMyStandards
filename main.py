#!/usr/bin/env python3
"""
Main entry point for MapMyStandards SaaS API on Railway.
This file ensures Railway runs the correct application.
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting MapMyStandards SaaS API...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

try:
    print("📦 Importing SaaS API...")
    from saas_api_safe import app
    print("✅ SaaS API imported successfully!")
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    
    if __name__ == "__main__":
        import uvicorn
        
        port = int(os.getenv("PORT", 8080))
        print(f"🌐 Starting server on port {port}")
        print("Available endpoints:")
        print("  GET  /health")
        print("  GET  /landing")
        print("  POST /trial/signup")
        print("  GET  /dashboard/{trial_id}")
        print("  POST /contact")
        print("  GET  /status")
        print("  GET  /docs (FastAPI documentation)")
        
        uvicorn.run(app, host="0.0.0.0", port=port)
        
except Exception as e:
    print(f"❌ Error importing SaaS API: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
