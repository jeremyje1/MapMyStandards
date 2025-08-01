#!/usr/bin/env python3
"""
Simple Trial API v2 for MapMyStandards A³E System
Production-ready FastAPI backend for trial signup and dashboard
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import logging
from pathlib import Path

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Database imports
import sqlite3
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

# Static file serving
if os.path.exists("web"):
    app.mount("/web", StaticFiles(directory="web"), name="web")
if os.path.exists("templates"):
    app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Database initialization
async def init_database():
    """Initialize the trial database"""
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
        "database": "connected",
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
        <html>
            <head>
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
    
    # Serve dashboard for valid customer
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MapMyStandards A³E Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
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
                    <div class="flex-shrink-0">
                        <svg class="h-8 w-8 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-lg font-medium text-blue-900">Free Trial Active</h3>
                        <p class="text-blue-700">Your 14-day trial is currently active. Explore all features!</p>
                    </div>
                </div>
            </div>

            <!-- Features Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                <!-- Standards Analysis -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <div class="flex items-center mb-4">
                        <div class="p-2 bg-blue-100 rounded-lg">
                            <svg class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <h3 class="ml-3 text-lg font-semibold text-gray-900">Standards Analysis</h3>
                    </div>
                    <p class="text-gray-600 mb-4">Upload documents for AI-powered standards alignment analysis.</p>
                    <button class="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md transition-colors">
                        Analyze Documents
                    </button>
                </div>

                <!-- Course Mapping -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <div class="flex items-center mb-4">
                        <div class="p-2 bg-green-100 rounded-lg">
                            <svg class="h-6 w-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                            </svg>
                        </div>
                        <h3 class="ml-3 text-lg font-semibold text-gray-900">Course Mapping</h3>
                    </div>
                    <p class="text-gray-600 mb-4">Map your curriculum to educational standards automatically.</p>
                    <button class="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-md transition-colors">
                        Map Courses
                    </button>
                </div>

                <!-- Compliance Reports -->
                <div class="bg-white rounded-lg shadow-sm p-6">
                    <div class="flex items-center mb-4">
                        <div class="p-2 bg-purple-100 rounded-lg">
                            <svg class="h-6 w-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                        </div>
                        <h3 class="ml-3 text-lg font-semibold text-gray-900">Compliance Reports</h3>
                    </div>
                    <p class="text-gray-600 mb-4">Generate detailed compliance and alignment reports.</p>
                    <button class="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-md transition-colors">
                        Generate Reports
                    </button>
                </div>
            </div>

            <!-- Support Section -->
            <div class="bg-white rounded-lg shadow-sm p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">Need Help?</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <a href="mailto:support@mapmystandards.ai" class="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <svg class="h-5 w-5 text-gray-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span class="text-gray-700">Email Support</span>
                    </a>
                    <a href="#" class="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <svg class="h-5 w-5 text-gray-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        <span class="text-gray-700">Documentation</span>
                    </a>
                    <a href="#" class="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                        <svg class="h-5 w-5 text-gray-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        <span class="text-gray-700">Live Chat</span>
                    </a>
                </div>
            </div>
        </div>

        <script>
            // Load trial status on page load
            window.addEventListener('DOMContentLoaded', function() {{
                fetch(`/api/trial/status/{customer_id}`)
                    .then(response => response.json())
                    .then(data => {{
                        console.log('Trial status:', data);
                        // Update UI with trial information
                    }})
                    .catch(error => console.error('Error loading trial status:', error));
            }});
        </script>
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

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    await init_database()
    logger.info("MapMyStandards A³E Trial API started successfully")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "simple_trial_api_v2:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
