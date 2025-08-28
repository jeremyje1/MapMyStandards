#!/usr/bin/env python3
"""
Test server with billing endpoints for trial signup testing
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import uvicorn
import os
import sys

# Add current directory to Python path to import the billing module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Trial Billing Test Server", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import billing routes
try:
    from src.a3e.api.routes.billing import router as billing_router
    app.include_router(billing_router)
    print("✅ Billing routes loaded successfully")
except Exception as e:
    print(f"❌ Failed to load billing routes: {e}")
    
    # Create minimal mock endpoints for testing
    @app.get("/api/v1/billing/config/stripe-key")
    async def get_stripe_key():
        return {
            "publishable_key": "pk_test_51RyQzQK8PKpLCKDZHK9fNhQZxvv6K0Yo8LTZx8wkd7mzAyIx4vFvF5oIlFwXU8cKF6jR4VFpv3ZF8sE6YnGGGG7A00LF3vBrPv",
            "environment": "test"
        }
    
    @app.post("/api/v1/billing/trial/signup")
    async def trial_signup_mock(request: dict):
        print(f"Mock trial signup received: {request}")
        return {
            "success": True,
            "message": "7-day free trial started successfully",
            "trial_id": "sub_test123",
            "data": {
                "api_key": "a3e_test123",
                "trial_end": "2025-09-04T19:20:00",
                "customer_id": "cus_test123", 
                "subscription_id": "sub_test123",
                "plan": request.get("plan", "college_monthly"),
                "status": "trialing",
                "billing_starts": "2025-09-04T19:20:00"
            }
        }

# Serve static files
try:
    app.mount("/", StaticFiles(directory="web", html=True), name="web")
    print("✅ Static files mounted from /web")
except Exception as e:
    print(f"⚠️ Could not mount static files: {e}")

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head><title>Trial Billing Test Server</title></head>
        <body>
            <h1>MapMyStandards Trial Test Server</h1>
            <p>Server is running!</p>
            <ul>
                <li><a href="/trial-signup.html">Trial Signup Page</a></li>
                <li><a href="/docs">API Documentation</a></li>
                <li><a href="/api/v1/billing/config/stripe-key">Test Stripe Key Endpoint</a></li>
            </ul>
        </body>
    </html>
    """)

if __name__ == "__main__":
    print("🚀 Starting Trial Billing Test Server")
    print("📋 Trial signup: http://localhost:8000/trial-signup.html")
    print("📖 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "test_billing_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )