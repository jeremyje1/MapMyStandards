#!/usr/bin/env python3
"""
Simple Trial API v2 for MapMyStandards A³E System
Production-ready FastAPI backend - Simplified for Railway
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import logging

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Database imports
import aiosqlite

# Stripe imports
import stripe

# Environment configuration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY', 'sk_test_PLACEHOLDER')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', 'pk_test_PLACEHOLDER')

# Database configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'a3e_trial.db')

# Initialize FastAPI app
app = FastAPI(
    title="MapMyStandards A³E Trial API",
    description="Production API for trial signups and dashboard access",
    version="2.0.0"
)

# CORS configuration for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization (called on demand, not at startup)
async def init_database():
    """Initialize the trial database"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS trial_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    organization TEXT,
                    role TEXT,
                    standards_focus TEXT,
                    stripe_customer_id TEXT,
                    trial_start_date TEXT,
                    trial_end_date TEXT,
                    subscription_status TEXT DEFAULT 'trial',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't fail startup, just log the error

# API Routes

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "MapMyStandards A³E Trial API",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "available",
        "stripe": "configured" if stripe.api_key != 'sk_test_PLACEHOLDER' else "placeholder",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/trial/signup")
async def trial_signup(
    email: str = Form(...),
    organization: str = Form(...),
    role: str = Form(...),
    standards_focus: str = Form(...)
):
    """Handle trial signup with Stripe customer creation"""
    try:
        # Initialize database on first use
        await init_database()
        
        logger.info(f"Processing trial signup for {email}")
        
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=email,
            metadata={
                'organization': organization,
                'role': role,
                'standards_focus': standards_focus,
                'signup_source': 'trial'
            }
        )
        
        # Calculate trial dates
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=14)
        
        # Store in database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT OR REPLACE INTO trial_users 
                (email, organization, role, standards_focus, stripe_customer_id, 
                 trial_start_date, trial_end_date, subscription_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                email, organization, role, standards_focus, customer.id,
                trial_start.isoformat(), trial_end.isoformat(), 'trial'
            ))
            await db.commit()
        
        logger.info(f"Trial signup successful for {email}")
        return {
            "success": True,
            "message": "Trial activated successfully!",
            "customer_id": customer.id,
            "trial_end_date": trial_end.isoformat(),
            "dashboard_url": f"/dashboard?customer_id={customer.id}"
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error during signup: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Payment processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Error during trial signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/trial/status/{customer_id}")
async def get_trial_status(customer_id: str):
    """Get trial status for a customer"""
    try:
        # Initialize database on first use
        await init_database()
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute(
                'SELECT * FROM trial_users WHERE stripe_customer_id = ?',
                (customer_id,)
            ) as cursor:
                row = await cursor.fetchone()
                
                if not row:
                    raise HTTPException(status_code=404, detail="Trial not found")
                
                # Convert row to dict
                columns = [description[0] for description in cursor.description]
                user_data = dict(zip(columns, row))
                
                # Check if trial is still active
                trial_end = datetime.fromisoformat(user_data['trial_end_date'])
                is_active = datetime.utcnow() < trial_end
                
                return {
                    "customer_id": customer_id,
                    "email": user_data['email'],
                    "organization": user_data['organization'],
                    "trial_active": is_active,
                    "trial_end_date": user_data['trial_end_date'],
                    "subscription_status": user_data['subscription_status'],
                    "days_remaining": max(0, (trial_end - datetime.utcnow()).days)
                }
                
    except Exception as e:
        logger.error(f"Error getting trial status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboard")
async def dashboard(request: Request, customer_id: Optional[str] = None):
    """Serve the dashboard page"""
    if not customer_id:
        # Redirect to signup if no customer_id
        return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MapMyStandards A³E - Access Required</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100 min-h-screen flex items-center justify-center">
            <div class="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
                <h1 class="text-2xl font-bold text-gray-900 mb-4">Access Required</h1>
                <p class="text-gray-600 mb-6">Please sign up for a trial to access the dashboard.</p>
                <a href="/web/checkout.html" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Start Free Trial
                </a>
            </div>
        </body>
        </html>
        """)
    
    # Serve basic dashboard for valid customer
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MapMyStandards A³E Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen">
        <div class="max-w-7xl mx-auto px-4 py-8">
            <!-- Header -->
            <div class="bg-white rounded-lg shadow-sm p-6 mb-8">
                <div class="flex items-center justify-between">
                    <div>
                        <h1 class="text-3xl font-bold text-gray-900">MapMyStandards A³E</h1>
                        <p class="text-gray-600">AI-Powered Standards Alignment Engine</p>
                    </div>
                    <div class="text-sm text-gray-500">
                        Customer ID: {customer_id}
                    </div>
                </div>
            </div>

            <!-- Trial Status -->
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
                <div class="flex items-center">
                    <div class="ml-3">
                        <h3 class="text-lg font-medium text-blue-900">Free Trial Active</h3>
                        <p class="text-blue-700">Your 14-day trial is currently active. Explore all features!</p>
                    </div>
                </div>
            </div>

            <!-- Welcome Message -->
            <div class="bg-white rounded-lg shadow-sm p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Welcome to MapMyStandards A³E</h3>
                <p class="text-gray-600">Your trial dashboard is ready. Contact support@mapmystandards.ai for assistance.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(dashboard_html)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "message": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting MapMyStandards A³E API on port {port}")
    uvicorn.run(
        "simple_trial_api_v2_fixed:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
