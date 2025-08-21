#!/usr/bin/env python3
"""
Working SaaS API for MapMyStandards A³E System
Based on the successful ultra-minimal API structure
"""

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app (same as working minimal version)
app = FastAPI(title="MapMyStandards A³E SaaS API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo (no database complexity)
trial_users = {}

@app.get("/")
def root():
    """Root endpoint - same as working minimal version"""
    return {
        "status": "healthy",
        "service": "MapMyStandards A³E SaaS API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
def health():
    """Health check - same as working minimal version"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/api/trial/signup")
async def trial_signup(
    email: str = Form(...),
    organization: str = Form(...),
    role: str = Form(...),
    standards_focus: str = Form(...)
):
    """Simple trial signup without external dependencies"""
    try:
        logger.info(f"Processing trial signup for {email}")
        
        # Generate simple customer ID
        customer_id = f"cus_{len(trial_users) + 1}_{email.split('@')[0]}"
        
        # Calculate trial dates
        trial_start = datetime.utcnow()
        trial_end = trial_start + timedelta(days=14)
        
        # Store in memory
        trial_users[customer_id] = {
            "email": email,
            "organization": organization,
            "role": role,
            "standards_focus": standards_focus,
            "trial_start": trial_start.isoformat(),
            "trial_end": trial_end.isoformat(),
            "status": "active"
        }
        
        logger.info(f"Trial signup successful for {email}")
        return {
            "success": True,
            "message": "Trial activated successfully!",
            "customer_id": customer_id,
            "trial_end_date": trial_end.isoformat(),
            "dashboard_url": f"/dashboard?customer_id={customer_id}"
        }
        
    except Exception as e:
        logger.error(f"Error during trial signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/trial/status/{customer_id}")
async def get_trial_status(customer_id: str):
    """Get trial status for a customer"""
    try:
        if customer_id not in trial_users:
            raise HTTPException(status_code=404, detail="Trial not found")
        
        user_data = trial_users[customer_id]
        trial_end = datetime.fromisoformat(user_data['trial_end'])
        is_active = datetime.utcnow() < trial_end
        
        return {
            "customer_id": customer_id,
            "email": user_data['email'],
            "organization": user_data['organization'],
            "trial_active": is_active,
            "trial_end_date": user_data['trial_end'],
            "subscription_status": user_data['status'],
            "days_remaining": max(0, (trial_end - datetime.utcnow()).days)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trial status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/dashboard")
async def dashboard(customer_id: Optional[str] = None):
    """Serve the dashboard page"""
    if not customer_id:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MapMyStandards A³E - Access Required</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
                .btn { background: #007cba; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }
            </style>
        </head>
        <body>
            <h1>MapMyStandards A³E</h1>
            <p>Please sign up for a trial to access the dashboard.</p>
            <a href="/web/checkout.html" class="btn">Start Free Trial</a>
        </body>
        </html>
        """)
    
    # Check if customer exists
    if customer_id not in trial_users:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Trial Not Found</title></head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
            <h1>Trial Not Found</h1>
            <p>The trial you're looking for doesn't exist.</p>
        </body>
        </html>
        """)
    
    user_data = trial_users[customer_id]
    trial_end = datetime.fromisoformat(user_data['trial_end'])
    days_remaining = max(0, (trial_end - datetime.utcnow()).days)
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MapMyStandards A³E Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .status {{ background: #e7f3ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
            .feature {{ background: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>MapMyStandards A³E Dashboard</h1>
            <p>AI-Powered Standards Alignment Engine</p>
            <small>Customer ID: {customer_id}</small>
        </div>
        
        <div class="status">
            <h3>Trial Status: Active</h3>
            <p><strong>Organization:</strong> {user_data['organization']}</p>
            <p><strong>Days Remaining:</strong> {days_remaining}</p>
            <p><strong>Trial Expires:</strong> {trial_end.strftime('%B %d, %Y')}</p>
        </div>
        
        <div class="feature">
            <h3>🔍 Standards Analysis</h3>
            <p>Upload documents for AI-powered standards alignment analysis.</p>
            <button onclick="alert('Feature coming soon!')">Analyze Documents</button>
        </div>
        
        <div class="feature">
            <h3>📚 Course Mapping</h3>
            <p>Map your curriculum to educational standards automatically.</p>
            <button onclick="alert('Feature coming soon!')">Map Courses</button>
        </div>
        
        <div class="feature">
            <h3>📊 Compliance Reports</h3>
            <p>Generate detailed compliance and alignment reports.</p>
            <button onclick="alert('Feature coming soon!')">Generate Reports</button>
        </div>
        
        <div class="feature">
            <h3>🆘 Support</h3>
            <p>Need help? Contact our support team.</p>
            <a href="mailto:support@mapmystandards.ai">support@mapmystandards.ai</a>
        </div>
        
        <script>
            // Load trial status
            fetch('/api/trial/status/{customer_id}')
                .then(response => response.json())
                .then(data => console.log('Trial status:', data))
                .catch(error => console.error('Error:', error));
        </script>
    </body>
    </html>
    """)

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "message": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Starting MapMyStandards A³E SaaS API on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
