from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uvicorn
import os
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MapMyStandards SaaS API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for trial users
trial_users: Dict[str, dict] = {}

# Email configuration (with fallbacks)
SMTP_SERVER = os.getenv("SMTP_SERVER", "mx1.titan.email")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "support@mapmystandards.ai")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "Ipo4Eva45*")

# Stripe configuration
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")

# Pydantic models
class TrialSignup(BaseModel):
    email: EmailStr
    name: str
    organization: Optional[str] = None
    use_case: Optional[str] = None

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str
    subject: Optional[str] = "Contact from MapMyStandards"

# Email sending function with error handling
async def send_email(to_email: str, subject: str, html_content: str, text_content: str = None):
    """Send an email using the configured SMTP settings"""
    try:
        # Try to import aiosmtplib only when needed
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = SMTP_USERNAME
        message["To"] = to_email

        # Add text version if provided
        if text_content:
            text_part = MIMEText(text_content, "plain")
            message.attach(text_part)

        # Add HTML version
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send the email
        await aiosmtplib.send(
            message,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USERNAME,
            password=SMTP_PASSWORD,
            timeout=10,  # Add timeout
        )
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except ImportError as e:
        logger.error(f"Email library not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Email sending failed: {e}")
        return False

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 MapMyStandards SaaS API starting up...")
    logger.info(f"📧 Email configured: {SMTP_USERNAME}@{SMTP_SERVER}:{SMTP_PORT}")

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "MapMyStandards SaaS API", 
        "status": "live", 
        "version": "1.0.0",
        "features": ["trial_signup", "dashboard", "email_integration"],
        "endpoints": ["/health", "/config/stripe-key", "/landing", "/trial/signup", "/dashboard/{trial_id}", "/contact", "/pricing"]
    }

# Health check
@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "api_version": "1.0.0",
        "active_trials": len(trial_users)
    }

# Stripe configuration endpoint
@app.get("/config/stripe-key")
def get_stripe_key():
    """Return the Stripe publishable key for frontend use"""
    if not STRIPE_PUBLISHABLE_KEY:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Only return publishable key (safe for frontend)
    return {
        "publishable_key": STRIPE_PUBLISHABLE_KEY,
        "environment": "live" if STRIPE_PUBLISHABLE_KEY.startswith("pk_live_") else "test"
    }

# Landing page
@app.get("/landing", response_class=HTMLResponse)
def landing_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MapMyStandards.ai - Autonomous Accreditation Engine</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { text-align: center; color: white; padding: 50px 0; }
            .header h1 { font-size: 3em; margin-bottom: 10px; }
            .header p { font-size: 1.2em; opacity: 0.9; }
            .content { background: white; border-radius: 15px; padding: 40px; margin-top: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
            .trial-form { background: #f8f9fa; padding: 30px; border-radius: 10px; margin: 30px 0; }
            .form-group { margin-bottom: 20px; }
            .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
            .form-group input, .form-group textarea, .form-group select { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; box-sizing: border-box; }
            .btn { background: #667eea; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
            .btn:hover { background: #5a6fd8; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; margin: 40px 0; }
            .feature { text-align: center; padding: 20px; }
            .feature h3 { color: #333; margin-bottom: 15px; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>MapMyStandards.ai</h1>
                <p>Autonomous Accreditation & Audit Engine</p>
                <p>Transform your compliance workflows with AI-powered automation</p>
            </div>
            
            <div class="content">
                <h2>Start Your Free Trial</h2>
                <p>Experience the power of automated accreditation mapping and audit preparation.</p>
                
                <div class="trial-form">
                    <form id="trialForm">
                        <div class="form-group">
                            <label for="name">Full Name</label>
                            <input type="text" id="name" name="name" required>
                        </div>
                        <div class="form-group">
                            <label for="email">Email Address</label>
                            <input type="email" id="email" name="email" required>
                        </div>
                        <div class="form-group">
                            <label for="organization">Organization (Optional)</label>
                            <input type="text" id="organization" name="organization">
                        </div>
                        <div class="form-group">
                            <label for="use_case">Primary Use Case</label>
                            <select id="use_case" name="use_case">
                                <option value="">Select your primary interest...</option>
                                <option value="accreditation">Accreditation Preparation</option>
                                <option value="compliance">Compliance Monitoring</option>
                                <option value="audit">Audit Automation</option>
                                <option value="mapping">Standards Mapping</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">Start Free Trial</button>
                    </form>
                    <div id="status"></div>
                </div>

                <div class="features">
                    <div class="feature">
                        <h3>🤖 AI-Powered Analysis</h3>
                        <p>Automatically map your processes to accreditation standards using advanced AI</p>
                    </div>
                    <div class="feature">
                        <h3>📊 Real-time Dashboard</h3>
                        <p>Monitor compliance status and track progress with intuitive visualizations</p>
                    </div>
                    <div class="feature">
                        <h3>⚡ Rapid Deployment</h3>
                        <p>Get started in minutes with our streamlined onboarding process</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
            document.getElementById('trialForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = '<div class="status">Processing your request...</div>';
                
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/trial/signup', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        statusDiv.innerHTML = `
                            <div class="status success">
                                <strong>Success!</strong> Welcome to MapMyStandards! 
                                ${result.email_sent ? 'Check your email for access instructions.' : 'Your trial is ready!'}
                                <br><br>
                                <a href="/dashboard/${result.trial_id}" class="btn">Go to Dashboard</a>
                            </div>
                        `;
                        e.target.reset();
                    } else {
                        statusDiv.innerHTML = `<div class="status error"><strong>Error:</strong> ${result.detail}</div>`;
                    }
                } catch (error) {
                    statusDiv.innerHTML = '<div class="status error"><strong>Error:</strong> Something went wrong. Please try again.</div>';
                }
            });
        </script>
    </body>
    </html>
    """

# Trial signup endpoint
@app.post("/trial/signup")
async def trial_signup(signup: TrialSignup):
    """Create a new trial account"""
    try:
        logger.info(f"Trial signup attempt for {signup.email}")
        
        # Check if email already exists
        existing_user = next((user for user in trial_users.values() if user["email"] == signup.email), None)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered for trial")
        
        # Create trial user
        trial_id = str(uuid.uuid4())
        trial_data = {
            "trial_id": trial_id,
            "email": signup.email,
            "name": signup.name,
            "organization": signup.organization,
            "use_case": signup.use_case,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(days=14)).isoformat(),
            "status": "active"
        }
        
        trial_users[trial_id] = trial_data
        logger.info(f"Trial created successfully: {trial_id}")
        
        # Try to send welcome email (non-blocking)
        email_sent = False
        try:
            welcome_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white;">
                    <h1>Welcome to MapMyStandards.ai!</h1>
                    <p>Your 14-day free trial has started</p>
                </div>
                
                <div style="padding: 30px;">
                    <h2>Hello {signup.name}!</h2>
                    
                    <p>Thank you for starting your free trial with MapMyStandards.ai. You now have access to our autonomous accreditation and audit engine.</p>
                    
                    <h3>Your Trial Details:</h3>
                    <ul>
                        <li><strong>Trial ID:</strong> {trial_id}</li>
                        <li><strong>Started:</strong> {datetime.now().strftime('%B %d, %Y')}</li>
                        <li><strong>Expires:</strong> {(datetime.now() + timedelta(days=14)).strftime('%B %d, %Y')}</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="#" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Access Your Dashboard
                        </a>
                    </div>
                    
                    <p>Need help? Reply to this email or contact us at support@mapmystandards.ai</p>
                </div>
            </body>
            </html>
            """
            
            email_sent = await send_email(
                signup.email,
                "Welcome to MapMyStandards.ai - Your Trial Has Started!",
                welcome_html
            )
        except Exception as e:
            logger.warning(f"Email sending failed, but trial created: {e}")
        
        return {
            "success": True,
            "trial_id": trial_id,
            "message": "Trial account created successfully",
            "email_sent": email_sent,
            "expires_at": trial_data["expires_at"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trial signup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create trial account: {str(e)}")

# Trial dashboard
@app.get("/dashboard/{trial_id}", response_class=HTMLResponse)
def trial_dashboard(trial_id: str):
    """Display the trial user dashboard"""
    if trial_id not in trial_users:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    user = trial_users[trial_id]
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - MapMyStandards.ai</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 0; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .welcome {{ text-align: center; margin-bottom: 30px; }}
            .dashboard-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            .card h3 {{ margin-top: 0; color: #333; }}
            .status-badge {{ padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }}
            .active {{ background: #d4edda; color: #155724; }}
            .btn {{ background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; display: inline-block; }}
            .btn:hover {{ background: #5a6fd8; }}
            .metric {{ text-align: center; margin: 20px 0; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
            .metric-label {{ color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>MapMyStandards.ai Dashboard</h1>
                <p>Autonomous Accreditation & Audit Engine</p>
            </div>
        </div>
        
        <div class="container">
            <div class="welcome">
                <h2>Welcome back, {user['name']}!</h2>
                <p>Trial Status: <span class="status-badge active">Active</span></p>
                <p>Expires: {user['expires_at'][:10]}</p>
            </div>
            
            <div class="dashboard-grid">
                <div class="card">
                    <h3>🎯 Compliance Overview</h3>
                    <div class="metric">
                        <div class="metric-value">0%</div>
                        <div class="metric-label">Standards Mapped</div>
                    </div>
                    <p>Start by uploading your organizational documents to begin automated compliance analysis.</p>
                    <a href="#" class="btn">Upload Documents</a>
                </div>
                
                <div class="card">
                    <h3>📊 Audit Readiness</h3>
                    <div class="metric">
                        <div class="metric-value">0</div>
                        <div class="metric-label">Evidence Items</div>
                    </div>
                    <p>Our AI will automatically identify and catalog evidence for your compliance requirements.</p>
                    <a href="#" class="btn">View Evidence</a>
                </div>
                
                <div class="card">
                    <h3>🤖 AI Recommendations</h3>
                    <div class="metric">
                        <div class="metric-value">3</div>
                        <div class="metric-label">New Suggestions</div>
                    </div>
                    <p>Get personalized recommendations to improve your compliance posture.</p>
                    <a href="#" class="btn">View Recommendations</a>
                </div>
                
                <div class="card">
                    <h3>📅 Next Steps</h3>
                    <ul>
                        <li>Complete your organization profile</li>
                        <li>Upload policy documents</li>
                        <li>Review AI-generated mappings</li>
                        <li>Schedule implementation call</li>
                    </ul>
                    <a href="#" class="btn">Get Started</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# Contact form endpoint
@app.post("/contact")
async def contact_form(contact: ContactForm):
    """Handle contact form submissions"""
    try:
        logger.info(f"Contact form submission from {contact.email}")
        
        # Try to send notification email
        formatted_message = contact.message.replace('\n', '<br>')
        email_sent = await send_email(
            SMTP_USERNAME,
            f"Contact Form: {contact.subject}",
            f"""
            <h2>New Contact Form Submission</h2>
            <p><strong>Name:</strong> {contact.name}</p>
            <p><strong>Email:</strong> {contact.email}</p>
            <p><strong>Subject:</strong> {contact.subject}</p>
            <h3>Message:</h3>
            <div style="background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea;">
                {formatted_message}
            </div>
            """
        )
        
        return {
            "success": True,
            "message": "Contact form submitted successfully",
            "email_sent": email_sent
        }
        
    except Exception as e:
        logger.error(f"Contact form failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send contact form: {str(e)}")

# List trials (for admin/testing)
@app.get("/admin/trials")
def list_trials():
    """List all trial users (for testing)"""
    return {"total_trials": len(trial_users), "trials": trial_users}

# API status endpoint
@app.get("/status")
def api_status():
    """Detailed API status"""
    return {
        "api": "MapMyStandards SaaS",
        "version": "1.0.0",
        "status": "operational",
        "features": {
            "trial_signup": True,
            "email_integration": True,
            "dashboard": True,
            "contact_forms": True
        },
        "metrics": {
            "total_trials": len(trial_users),
            "active_trials": len([t for t in trial_users.values() if t["status"] == "active"])
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
