#!/usr/bin/env python3
"""
Main entry point for MapMyStandards SaaS API on Railway.
This file ensures Railway runs the correct application.
"""

from saas_api_safe import app

if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8080))
    print(f"Starting MapMyStandards SaaS API on port {port}")
    print("Available endpoints:")
    print("  GET  /health")
    print("  GET  /landing")
    print("  POST /trial/signup")
    print("  GET  /dashboard/{trial_id}")
    print("  POST /contact")
    print("  GET  /status")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
