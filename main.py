#!/usr/bin/env python3
"""
Main entry point for MapMyStandards A3E FastAPI application.
This file ensures Railway runs the correct application.
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🚀 Starting MapMyStandards A3E FastAPI Application...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

try:
    print("📦 Importing A3E FastAPI app...")
    from src.a3e.main import app
    print("✅ A3E FastAPI app imported successfully!")
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    
    # Export app for gunicorn/uvicorn
    __all__ = ['app']
    
    if __name__ == "__main__":
        import uvicorn
        
        port = int(os.getenv("PORT", 8080))
        print(f"🌐 Starting server on port {port}")
        print("Available endpoints:")
        print("  GET  /health")
        print("  GET  /docs (FastAPI documentation)")
        print("  POST /api/trial/signup")
        print("  POST /api/auth/login") 
        print("  GET  /api/dashboard/overview")
        print("  And more...")
        
        uvicorn.run(app, host="0.0.0.0", port=port)
        
except Exception as e:
    print(f"❌ Error importing A3E FastAPI app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
