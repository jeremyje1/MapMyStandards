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
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")

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
    logger.info(f"💳 Stripe configured: {'✅' if STRIPE_PUBLISHABLE_KEY else '❌'}")

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

# Debug endpoint to check environment variables
@app.get("/debug/env")
def debug_env():
    """Debug endpoint to check if environment variables are loaded"""
    return {
        "stripe_key_set": bool(STRIPE_PUBLISHABLE_KEY),
        "stripe_key_length": len(STRIPE_PUBLISHABLE_KEY) if STRIPE_PUBLISHABLE_KEY else 0,
        "stripe_key_prefix": STRIPE_PUBLISHABLE_KEY[:10] if STRIPE_PUBLISHABLE_KEY else "none"
    }

# Landing page
@app.get("/landing", response_class=HTMLResponse)
def landing_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Start Your Free Trial - MapMyStandards.ai</title>
    <script src="https://js.stripe.com/v3/"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 2rem; text-align: center; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        .content { padding: 2rem; }
        .trial-info { background: #e8f5e8; border-left: 4px solid #28a745; padding: 1.5rem; margin-bottom: 2rem; border-radius: 5px; }
        .trial-info h3 { color: #155724; margin-bottom: 0.5rem; }
        .trial-info p { color: #155724; margin-bottom: 0.5rem; }
        .pricing-options { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 2rem 0; }
        .pricing-card { border: 2px solid #e9ecef; border-radius: 10px; padding: 2rem; text-align: center; transition: all 0.3s; cursor: pointer; }
        .pricing-card:hover { border-color: #667eea; transform: translateY(-5px); }
        .pricing-card.selected { border-color: #667eea; background: #f8f9ff; }
        .plan-name { font-size: 1.5rem; font-weight: 700; color: #2c3e50; margin-bottom: 1rem; }
        .plan-price { font-size: 2.5rem; font-weight: 700; color: #667eea; margin-bottom: 0.5rem; }
        .plan-period { color: #6c757d; margin-bottom: 1.5rem; }
        .plan-features { list-style: none; margin-bottom: 1.5rem; }
        .plan-features li { padding: 0.3rem 0; padding-left: 1.5rem; position: relative; text-align: left; }
        .plan-features li::before { content: "✓"; position: absolute; left: 0; color: #27ae60; font-weight: bold; }
        .checkout-section { background: #f8f9fa; padding: 2rem; border-radius: 10px; margin-top: 2rem; text-align: center; }
        .checkout-button { background: #28a745; color: white; border: none; padding: 1rem 3rem; font-size: 1.2rem; border-radius: 50px; cursor: pointer; font-weight: 600; transition: all 0.3s; width: 100%; max-width: 400px; }
        .checkout-button:hover { background: #218838; transform: translateY(-2px); }
        .checkout-button:disabled { background: #6c757d; cursor: not-allowed; transform: none; }
        .security-info { margin-top: 1rem; font-size: 0.9rem; color: #6c757d; }
        .error-message { background: #f8d7da; color: #721c24; padding: 1rem; border-radius: 5px; margin: 1rem 0; display: none; }
        @media (max-width: 768px) { .pricing-options { grid-template-columns: 1fr; } .header h1 { font-size: 2rem; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Start Your Free Trial</h1>
            <p>Get instant access to the A³E platform with full features</p>
        </div>
        <div class="content">
            <div class="trial-info">
                <h3>📅 7-Day Free Trial</h3>
                <p><strong>Free access for 7 days</strong> • Full features included • Credit card required</p>
                <p>Cancel anytime during trial with no charges • Billing starts automatically after trial period</p>
            </div>
            <h3 style="text-align: center; margin-bottom: 1.5rem;">Choose Your Plan</h3>
            <div class="pricing-options">
                <div class="pricing-card" onclick="selectPlan('college', 29700, 'monthly')" id="college-monthly">
                    <div class="plan-name">A³E College Plan</div>
                    <div class="plan-price">$297</div>
                    <div class="plan-period">per month</div>
                    <ul class="plan-features">
                        <li>Up to 3 campus profiles</li>
                        <li>Unlimited document analysis</li>
                        <li>Full AI pipeline</li>
                        <li>Canvas LMS integration</li>
                        <li>Email support</li>
                    </ul>
                </div>
                <div class="pricing-card" onclick="selectPlan('multicampus', 89700, 'monthly')" id="multicampus-monthly">
                    <div class="plan-name">A³E Multi-Campus</div>
                    <div class="plan-price">$897</div>
                    <div class="plan-period">per month</div>
                    <ul class="plan-features">
                        <li>Unlimited campus profiles</li>
                        <li>Everything in College Plan</li>
                        <li>API access (10K calls/month)</li>
                        <li>Dedicated success manager</li>
                        <li>Phone support</li>
                    </ul>
                </div>
            </div>
            <div class="error-message" id="error-message"></div>
            <div class="checkout-section">
                <button class="checkout-button" id="checkout-button" onclick="startCheckout()" disabled>
                    Select a plan to continue
                </button>
                <div class="security-info">
                    🔒 Secure checkout powered by Stripe • Your payment information is encrypted and secure
                </div>
            </div>
        </div>
    </div>
    <script>
        const stripe = Stripe('pk_live_51Rr4dNK8PKpLCKDZH9u9mOEqmPVSR946uGYKSdk73mmNjBR4i9Ibon3wvDLNpYPRzsXmaAXTrwSPKKxNolArj8G200tZyrr6qE');
        let selectedPlan = null; let selectedPrice = null; let selectedInterval = null;
        function selectPlan(plan, price, interval) {
            document.querySelectorAll('.pricing-card').forEach(card => card.classList.remove('selected'));
            document.getElementById(plan + '-' + interval).classList.add('selected');
            selectedPlan = plan; selectedPrice = price; selectedInterval = interval;
            const button = document.getElementById('checkout-button');
            button.disabled = false;
            button.textContent = "Start 7-Day Free Trial - $" + (price/100).toFixed(0) + "/" + interval;
        }
        async function startCheckout() {
            if (!selectedPlan) { showError('Please select a plan first'); return; }
            const button = document.getElementById('checkout-button');
            button.disabled = true; button.textContent = 'Creating checkout session...';
            try {
                const response = await fetch('/create-checkout-session', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ plan: selectedPlan, price_id: getPriceId(selectedPlan, selectedInterval), trial_days: 7 })
                });
                if (!response.ok) throw new Error('Failed to create checkout session');
                const session = await response.json();
                const result = await stripe.redirectToCheckout({ sessionId: session.id });
                if (result.error) throw new Error(result.error.message);
            } catch (error) {
                showError('Failed to start checkout: ' + error.message);
                button.disabled = false;
                button.textContent = "Start 7-Day Free Trial - $" + (selectedPrice/100).toFixed(0) + "/" + selectedInterval;
            }
        }
        function getPriceId(plan, interval) {
            const priceIds = { 'college_monthly': 'price_1Rr4y3K8PKpLCKDZqBXxFoG1', 'college_yearly': 'price_1Rr4y3K8PKpLCKDZOufRvjyV', 'multicampus_monthly': 'price_1Rr4y3K8PKpLCKDZXU67GOp2', 'multicampus_yearly': 'price_1Rr4y3K8PKpLCKDZEBQcMAh1' };
            return priceIds[plan + '_' + interval] || 'price_1Rr4y3K8PKpLCKDZqBXxFoG1';
        }
        function showError(message) {
            const errorDiv = document.getElementById('error-message');
            errorDiv.textContent = message; errorDiv.style.display = 'block';
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }
        const urlParams = new URLSearchParams(window.location.search);
        const planParam = urlParams.get('plan');
        if (planParam === 'college') selectPlan('college', 29700, 'monthly');
        else if (planParam === 'multicampus') selectPlan('multicampus', 89700, 'monthly');
    </script>
</body>
</html>"""


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
@app.get("/stripe-test")
def stripe_test():
    return {"stripe": "checkout test"}

# Stripe checkout endpoints
class CheckoutSessionRequest(BaseModel):
    plan: str
    price_id: str
    trial_days: int = 7

@app.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    """Create a Stripe checkout session for trial signup with credit card capture"""
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        
        if not stripe.api_key:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': request.price_id,
                'quantity': 1,
            }],
            subscription_data={
                'trial_period_days': request.trial_days,
                'metadata': {
                    'plan': request.plan,
                    'trial_days': request.trial_days
                }
            },
            success_url='https://api.mapmystandards.ai/trial/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://api.mapmystandards.ai/landing?cancelled=true',
            allow_promotion_codes=True,
            billing_address_collection='required',
        )
        
        return {"id": session.id, "url": session.url}
        
    except Exception as e:
        logger.error(f"Checkout session creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

@app.get("/trial/success", response_class=HTMLResponse)
async def trial_success_page(session_id: str = None):
    """Trial success page after Stripe checkout completion."""
    try:
        # Process the Stripe session and create user account
        if session_id:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
        
            
            try:
                # Retrieve the checkout session
                session = stripe.checkout.Session.retrieve(session_id)
                customer_id = session.customer
                subscription_id = session.subscription
                
                # Get customer details
                customer = stripe.Customer.retrieve(customer_id)
                email = customer.email
                
                # Generate trial ID and store user
                import secrets
                trial_id = secrets.token_urlsafe(16)
                trial_users[trial_id] = {
                    'name': customer.name or email.split('@')[0],
                    'email': email,
                    'organization': f"Customer {customer_id}",
                    'use_case': 'stripe_trial',
                    'created_at': datetime.now().isoformat(),
                    'stripe_customer_id': customer_id,
                    'stripe_subscription_id': subscription_id,
                    'trial_ends': (datetime.now() + timedelta(days=7)).isoformat()
                }
                
                # Return success page
                return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Welcome to A³E - Trial Started!</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 2rem; background: #f8f9fa; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 2rem; border-radius: 10px; }}
                        .success {{ color: #28a745; font-size: 2rem; margin-bottom: 1rem; }}
                        .btn {{ background: #007bff; color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 5px; display: inline-block; margin: 0.5rem; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="success">🎉 Welcome to A³E!</div>
                        <h1>Your 7-day free trial has started!</h1>
                        <p><strong>Email:</strong> {email}</p>
                        <p><strong>Trial ID:</strong> {trial_id}</p>
                        <p>Billing starts automatically on {(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}</p>
                        <a href="https://api.mapmystandards.ai/dashboard/{trial_id}" class="btn">🚀 Access Dashboard</a>
                        <a href="https://api.mapmystandards.ai/docs" class="btn">📖 API Docs</a>
                    </div>
                </body>
                </html>
                """)
                
            except Exception as e:
                logger.error(f"Error processing checkout session: {e}")
                return HTMLResponse(content=f"<h1>Error processing trial signup</h1><p>Session: {session_id}</p>", status_code=500)
        
        return HTMLResponse(content="<h1>Trial signup completed!</h1>")
        
    except Exception as e:
        logger.error(f"Trial success page error: {e}")
        return HTMLResponse(content="<h1>Error loading success page</h1>", status_code=500)

# Stripe webhook endpoint for billing events
@app.post("/api/v1/billing/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment events"""
    try:
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        # Import stripe only when needed
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        
        # Get webhook secret from environment
        webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
        
        if not webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not configured")
            # Process without signature verification in development
            event = json.loads(payload.decode('utf-8'))
        else:
            # Verify webhook signature
            try:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            except ValueError as e:
                logger.error(f"Invalid payload: {e}")
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Invalid signature: {e}")
                raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        event_type = event['type']
        logger.info(f"Processing webhook event: {event_type}")
        
        if event_type == 'checkout.session.completed':
            # Handle successful checkout
            session = event['data']['object']
            await _handle_checkout_completed(session)
            
        elif event_type == 'customer.subscription.created':
            # Handle new subscription
            subscription = event['data']['object']
            await _handle_subscription_created(subscription)
            
        elif event_type == 'customer.subscription.updated':
            # Handle subscription changes
            subscription = event['data']['object']
            await _handle_subscription_updated(subscription)
            
        elif event_type == 'customer.subscription.deleted':
            # Handle subscription cancellation
            subscription = event['data']['object']
            await _handle_subscription_deleted(subscription)
            
        elif event_type == 'invoice.payment_succeeded':
            # Handle successful payment
            invoice = event['data']['object']
            await _handle_payment_succeeded(invoice)
            
        elif event_type == 'invoice.payment_failed':
            # Handle failed payment
            invoice = event['data']['object']
            await _handle_payment_failed(invoice)
            
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return {"received": True, "event_type": event_type}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")

# Webhook event handlers
async def _handle_checkout_completed(session):
    """Handle successful checkout session completion"""
    customer_id = session.get('customer')
    subscription_id = session.get('subscription')
    logger.info(f"Checkout completed: customer {customer_id}, subscription {subscription_id}")
    
    # Create or update trial user record
    # This would typically involve:
    # 1. Creating user account
    # 2. Setting up trial period
    # 3. Sending welcome email
    # 4. Activating services

async def _handle_subscription_created(subscription):
    """Handle new subscription creation"""
    customer_id = subscription.get('customer')
    status = subscription.get('status')
    logger.info(f"Subscription created: {subscription.get('id')} for customer {customer_id}, status: {status}")

async def _handle_subscription_updated(subscription):
    """Handle subscription updates (trial ending, plan changes, etc.)"""
    customer_id = subscription.get('customer')
    status = subscription.get('status')
    logger.info(f"Subscription updated: {subscription.get('id')} for customer {customer_id}, status: {status}")

async def _handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')
    logger.info(f"Subscription cancelled: {subscription.get('id')} for customer {customer_id}")
    
    # Deactivate user account, clean up resources, etc.

async def _handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    amount = invoice.get('amount_paid', 0) / 100  # Convert from cents
    logger.info(f"Payment succeeded: ${amount} for customer {customer_id}")

async def _handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')
    amount = invoice.get('amount_due', 0) / 100  # Convert from cents
    logger.warning(f"Payment failed: ${amount} for customer {customer_id}")
    
    # Send notification, retry payment, or suspend account

@app.get("/debug/stripe")
async def debug_stripe():
    """Debug endpoint to check Stripe configuration"""
    return {
        "publishable_key_set": bool(STRIPE_PUBLISHABLE_KEY),
        "secret_key_set": bool(STRIPE_SECRET_KEY),
        "publishable_key_prefix": STRIPE_PUBLISHABLE_KEY[:7] if STRIPE_PUBLISHABLE_KEY else "None",
        "secret_key_prefix": STRIPE_SECRET_KEY[:7] if STRIPE_SECRET_KEY else "None"
    }


@app.get("/test/stripe-simple")
async def test_stripe_simple():
    """Simple Stripe test to verify library and credentials"""
    try:
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        # Try to list a few products to test the connection
        products = stripe.Product.list(limit=1)
        
        return {
            "stripe_library_imported": True,
            "api_key_set": bool(STRIPE_SECRET_KEY),
            "api_connection_test": "success",
            "product_count": len(products.data)
        }
    except Exception as e:
        return {
            "stripe_library_imported": True,
            "api_key_set": bool(STRIPE_SECRET_KEY),
            "api_connection_test": "failed",
            "error": str(e),
            "error_type": type(e).__name__
        }

# Document Upload Interface
@app.get("/upload", response_class=HTMLResponse)
async def upload_interface():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Upload Documents - A³E</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; }
            .container { max-width: 800px; margin: 0 auto; padding: 2rem; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; border-radius: 12px; margin-bottom: 2rem; }
            .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 2rem; }
            .upload-zone { border: 2px dashed #cbd5e0; border-radius: 8px; padding: 3rem; text-align: center; transition: all 0.3s; }
            .upload-zone:hover { border-color: #667eea; background: #f7fafc; }
            .btn { background: #667eea; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: 500; cursor: pointer; transition: all 0.3s; }
            .btn:hover { background: #5a67d8; transform: translateY(-1px); }
            .feature-list { list-style: none; }
            .feature-list li { padding: 0.5rem 0; padding-left: 2rem; position: relative; }
            .feature-list li::before { content: "✓"; position: absolute; left: 0; color: #48bb78; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📁 Document Upload Center</h1>
                <p>Upload your institutional documents for AI-powered standards analysis</p>
            </div>
            
            <div class="card">
                <h2>Upload Documents</h2>
                <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
                    <input type="file" id="fileInput" multiple accept=".pdf,.doc,.docx,.txt" style="display: none;" onchange="handleFileSelect(event)">
                    <div style="font-size: 2rem; margin-bottom: 1rem;">📎</div>
                    <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">Click to upload or drag files here</p>
                    <p style="color: #718096; font-size: 0.9rem;">Supports PDF, Word documents, and text files</p>
                </div>
                <div id="fileList" style="margin-top: 1rem;"></div>
                <button class="btn" onclick="processFiles()" id="processBtn" style="margin-top: 1rem;" disabled>
                    🚀 Process Documents
                </button>
            </div>
            
            <div class="card">
                <h2>What We Analyze</h2>
                <ul class="feature-list">
                    <li>Policy and procedure documents</li>
                    <li>Curriculum guides and syllabi</li>
                    <li>Assessment reports and outcomes</li>
                    <li>Faculty handbooks and guidelines</li>
                    <li>Strategic plans and institutional reports</li>
                    <li>Compliance documentation</li>
                </ul>
            </div>
            
            <div class="card">
                <h2>AI Analysis Features</h2>
                <ul class="feature-list">
                    <li>Automatic standards mapping to accreditation requirements</li>
                    <li>Evidence extraction and cataloging</li>
                    <li>Gap analysis and compliance scoring</li>
                    <li>Citation generation for audit trails</li>
                    <li>Actionable recommendations for improvement</li>
                </ul>
            </div>
        </div>
        
        <script>
            let selectedFiles = [];
            
            function handleFileSelect(event) {
                selectedFiles = Array.from(event.target.files);
                updateFileList();
                document.getElementById('processBtn').disabled = selectedFiles.length === 0;
            }
            
            function updateFileList() {
                const fileList = document.getElementById('fileList');
                if (selectedFiles.length === 0) {
                    fileList.innerHTML = '';
                    return;
                }
                
                fileList.innerHTML = '<h3>Selected Files:</h3>' + 
                    selectedFiles.map(file => 
                        `<div style="padding: 0.5rem; background: #f7fafc; margin: 0.5rem 0; border-radius: 4px;">
                            📄 ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)
                        </div>`
                    ).join('');
            }
            
            function processFiles() {
                if (selectedFiles.length === 0) return;
                
                // In a real implementation, this would upload files to the server
                alert(`Processing ${selectedFiles.length} files for AI analysis...\\n\\nThis is a demo interface. In the full platform, your documents would be uploaded securely and analyzed by our A³E engine.`);
                
                // Simulate processing
                document.getElementById('processBtn').innerHTML = '⏳ Processing...';
                document.getElementById('processBtn').disabled = true;
                
                setTimeout(() => {
                    alert('✅ Analysis complete! Your documents have been processed and mapped to relevant accreditation standards.');
                    window.location.href = '/evidence';
                }, 2000);
            }
        </script>
    </body>
    </html>
    """)

# Evidence Management Interface
@app.get("/evidence", response_class=HTMLResponse)
async def evidence_interface():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Evidence Management - A³E</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; border-radius: 12px; margin-bottom: 2rem; }
            .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 2rem; }
            .evidence-item { background: #f7fafc; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #667eea; }
            .standard-tag { background: #667eea; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; display: inline-block; margin: 0.25rem; }
            .confidence-bar { background: #e2e8f0; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 0.5rem; }
            .confidence-fill { background: #48bb78; height: 100%; transition: width 0.3s; }
            .btn { background: #667eea; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: 500; cursor: pointer; margin: 0.5rem; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Evidence Management</h1>
                <p>AI-cataloged evidence mapped to accreditation standards</p>
            </div>
            
            <div class="card">
                <h2>Evidence Summary</h2>
                <div class="grid">
                    <div style="text-align: center; padding: 1rem; background: #e6fffa; border-radius: 8px;">
                        <div style="font-size: 2rem; font-weight: bold; color: #319795;">127</div>
                        <div>Evidence Items</div>
                    </div>
                    <div style="text-align: center; padding: 1rem; background: #fef5e7; border-radius: 8px;">
                        <div style="font-size: 2rem; font-weight: bold; color: #d69e2e;">43</div>
                        <div>Standards Mapped</div>
                    </div>
                    <div style="text-align: center; padding: 1rem; background: #f0fff4; border-radius: 8px;">
                        <div style="font-size: 2rem; font-weight: bold; color: #38a169;">92%</div>
                        <div>Compliance Score</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Recent Evidence Items</h2>
                
                <div class="evidence-item">
                    <h3>Faculty Handbook - Section 3.2: Academic Policies</h3>
                    <p style="color: #718096; margin: 0.5rem 0;">Extracted from: Faculty_Handbook_2024.pdf</p>
                    <div style="margin: 0.5rem 0;">
                        <span class="standard-tag">SACSCOC 8.2.a</span>
                        <span class="standard-tag">SACSCOC 9.1</span>
                        <span class="standard-tag">AACSB A7</span>
                    </div>
                    <div>Confidence Score: 94%</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: 94%;"></div>
                    </div>
                </div>
                
                <div class="evidence-item">
                    <h3>Assessment Report - Learning Outcomes Analysis</h3>
                    <p style="color: #718096; margin: 0.5rem 0;">Extracted from: Annual_Assessment_Report_2024.pdf</p>
                    <div style="margin: 0.5rem 0;">
                        <span class="standard-tag">SACSCOC 8.2.a</span>
                        <span class="standard-tag">AACSB A4</span>
                    </div>
                    <div>Confidence Score: 87%</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: 87%;"></div>
                    </div>
                </div>
                
                <div class="evidence-item">
                    <h3>Strategic Plan - Institutional Effectiveness</h3>
                    <p style="color: #718096; margin: 0.5rem 0;">Extracted from: Strategic_Plan_2024-2029.pdf</p>
                    <div style="margin: 0.5rem 0;">
                        <span class="standard-tag">SACSCOC 5.1</span>
                        <span class="standard-tag">SACSCOC 7.3</span>
                    </div>
                    <div>Confidence Score: 91%</div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: 91%;"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Actions</h2>
                <a href="/upload" class="btn">📁 Upload More Documents</a>
                <a href="/recommendations" class="btn">🤖 View AI Recommendations</a>
                <a href="/export" class="btn">�� Export Evidence Report</a>
                <button class="btn" onclick="alert('Full search functionality coming soon!')">🔍 Search Evidence</button>
            </div>
        </div>
    </body>
    </html>
    """)

# AI Recommendations Interface
@app.get("/recommendations", response_class=HTMLResponse)
async def recommendations_interface():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Recommendations - A³E</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; }
            .container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; border-radius: 12px; margin-bottom: 2rem; }
            .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 2rem; }
            .recommendation { background: #f7fafc; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #f6ad55; }
            .priority-high { border-left-color: #f56565; }
            .priority-medium { border-left-color: #f6ad55; }
            .priority-low { border-left-color: #48bb78; }
            .priority-tag { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold; color: white; }
            .priority-high .priority-tag { background: #f56565; }
            .priority-medium .priority-tag { background: #f6ad55; }
            .priority-low .priority-tag { background: #48bb78; }
            .btn { background: #667eea; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: 500; cursor: pointer; margin: 0.5rem; }
            .action-list { list-style: none; margin-top: 1rem; }
            .action-list li { padding: 0.5rem 0; padding-left: 2rem; position: relative; }
            .action-list li::before { content: "→"; position: absolute; left: 0; color: #667eea; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Recommendations</h1>
                <p>Personalized suggestions to improve your accreditation compliance</p>
            </div>
            
            <div class="card">
                <h2>Priority Recommendations</h2>
                
                <div class="recommendation priority-high">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3>Missing Learning Outcomes Documentation</h3>
                        <span class="priority-tag">HIGH PRIORITY</span>
                    </div>
                    <p><strong>Standard:</strong> SACSCOC 8.2.a - Student Learning Outcomes</p>
                    <p style="margin: 1rem 0;">Our analysis indicates gaps in documented learning outcomes for 12 programs. This is critical for upcoming accreditation review.</p>
                    <ul class="action-list">
                        <li>Document specific learning outcomes for Business Administration program</li>
                        <li>Add assessment methods for Engineering Technology outcomes</li>
                        <li>Create outcome mapping for General Education requirements</li>
                    </ul>
                    <button class="btn" onclick="alert('Detailed action plan and templates would be provided here.')">📋 Get Action Plan</button>
                </div>
                
                <div class="recommendation priority-medium">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3>Faculty Qualifications Review Needed</h3>
                        <span class="priority-tag">MEDIUM PRIORITY</span>
                    </div>
                    <p><strong>Standard:</strong> SACSCOC 6.1 - Faculty</p>
                    <p style="margin: 1rem 0;">Faculty credential documentation could be strengthened to ensure compliance requirements are clearly met.</p>
                    <ul class="action-list">
                        <li>Update CV templates to highlight relevant qualifications</li>
                        <li>Document professional experience justifications</li>
                        <li>Create faculty qualification matrix by program</li>
                    </ul>
                    <button class="btn" onclick="alert('Faculty audit checklist and templates would be provided here.')">👥 Review Faculty Matrix</button>
                </div>
                
                <div class="recommendation priority-low">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                        <h3>Enhance Financial Resource Documentation</h3>
                        <span class="priority-tag">LOW PRIORITY</span>
                    </div>
                    <p><strong>Standard:</strong> SACSCOC 13.1 - Financial Resources</p>
                    <p style="margin: 1rem 0;">While compliant, financial planning documentation could provide stronger evidence of institutional stability.</p>
                    <ul class="action-list">
                        <li>Expand budget narrative documentation</li>
                        <li>Add multi-year financial projections</li>
                        <li>Document contingency planning processes</li>
                    </ul>
                    <button class="btn" onclick="alert('Financial documentation templates would be provided here.')">💰 View Templates</button>
                </div>
            </div>
            
            <div class="card">
                <h2>AI Insights</h2>
                <p>Based on analysis of your institutional documents and comparison with peer institutions:</p>
                <ul style="list-style: none; margin-top: 1rem;">
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>📊 Compliance Strength:</strong> Your institution excels in governance and administrative processes
                    </li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>🎯 Focus Area:</strong> Student success and outcomes assessment need attention
                    </li>
                    <li style="padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0;">
                        <strong>⏰ Timeline:</strong> Address high-priority items within 60 days for optimal compliance
                    </li>
                    <li style="padding: 0.5rem 0;">
                        <strong>🚀 Next Steps:</strong> Schedule implementation call to discuss customized action plans
                    </li>
                </ul>
            </div>
            
            <div class="card">
                <h2>Actions</h2>
                <a href="/evidence" class="btn">📊 Review Supporting Evidence</a>
                <a href="/upload" class="btn">📁 Upload Additional Documents</a>
                <a href="https://mapmystandards.ai/contact/" class="btn">📞 Schedule Consultation</a>
                <button class="btn" onclick="alert('Priority action plan would be generated and emailed.')">📧 Email Action Plan</button>
            </div>
        </div>
    </body>
    </html>
    """)

# Onboarding Interface
@app.get("/onboarding", response_class=HTMLResponse)
async def onboarding_interface():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Getting Started - A³E</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f8fafc; }
            .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; border-radius: 12px; margin-bottom: 2rem; }
            .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 2rem; }
            .step { background: #f7fafc; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #667eea; }
            .step-number { background: #667eea; color: white; width: 30px; height: 30px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 1rem; }
            .btn { background: #667eea; color: white; padding: 0.75rem 1.5rem; border: none; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: 500; cursor: pointer; margin: 0.5rem; }
            .checklist { list-style: none; }
            .checklist li { padding: 0.5rem 0; padding-left: 2rem; position: relative; }
            .checklist li::before { content: "☐"; position: absolute; left: 0; color: #667eea; font-size: 1.2rem; }
            .progress-bar { background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden; margin: 1rem 0; }
            .progress-fill { background: #48bb78; height: 100%; width: 25%; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Getting Started with A³E</h1>
                <p>Your step-by-step guide to accreditation automation success</p>
                <div style="margin-top: 1rem;">
                    <strong>Progress: 25% Complete</strong>
                    <div class="progress-bar">
                        <div class="progress-fill"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>Setup Steps</h2>
                
                <div class="step">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span class="step-number">1</span>
                        <h3>Institution Profile Setup</h3>
                        <span style="margin-left: auto; color: #48bb78; font-weight: bold;">✓ COMPLETE</span>
                    </div>
                    <p>Configure your institution details, accreditation requirements, and compliance timeline.</p>
                    <a href="#" class="btn" onclick="alert('Institution profile is already configured!')">✓ Completed</a>
                </div>
                
                <div class="step">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span class="step-number">2</span>
                        <h3>Upload Core Documents</h3>
                        <span style="margin-left: auto; color: #f6ad55; font-weight: bold;">IN PROGRESS</span>
                    </div>
                    <p>Upload your key institutional documents for AI analysis and standards mapping.</p>
                    <ul class="checklist">
                        <li>Faculty handbook and policies</li>
                        <li>Student handbook and catalog</li>
                        <li>Assessment and outcomes reports</li>
                        <li>Strategic plans and governance documents</li>
                    </ul>
                    <a href="/upload" class="btn">📁 Upload Documents</a>
                </div>
                
                <div class="step">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span class="step-number">3</span>
                        <h3>Review AI Analysis</h3>
                        <span style="margin-left: auto; color: #cbd5e0; font-weight: bold;">PENDING</span>
                    </div>
                    <p>Review AI-generated evidence mapping and compliance analysis results.</p>
                    <a href="/evidence" class="btn" disabled style="opacity: 0.5;">📊 Review Evidence</a>
                </div>
                
                <div class="step">
                    <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                        <span class="step-number">4</span>
                        <h3>Implement Recommendations</h3>
                        <span style="margin-left: auto; color: #cbd5e0; font-weight: bold;">PENDING</span>
                    </div>
                    <p>Act on AI recommendations to strengthen your compliance posture.</p>
                    <a href="/recommendations" class="btn" disabled style="opacity: 0.5;">🤖 View Recommendations</a>
                </div>
            </div>
            
            <div class="card">
                <h2>Quick Actions</h2>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="text-align: center; padding: 1rem; background: #e6fffa; border-radius: 8px;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📖</div>
                        <h3>User Guide</h3>
                        <a href="https://mapmystandards.ai/user-guide/" target="_blank" class="btn">Read Docs</a>
                    </div>
                    <div style="text-align: center; padding: 1rem; background: #fef5e7; border-radius: 8px;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">💬</div>
                        <h3>Get Support</h3>
                        <a href="https://mapmystandards.ai/contact/" target="_blank" class="btn">Contact Us</a>
                    </div>
                    <div style="text-align: center; padding: 1rem; background: #f0fff4; border-radius: 8px;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">📞</div>
                        <h3>Schedule Call</h3>
                        <a href="https://mapmystandards.ai/contact/" target="_blank" class="btn">Book Demo</a>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>What's Next?</h2>
                <p style="margin-bottom: 1rem;">Once you complete the initial setup:</p>
                <ul style="list-style-type: disc; padding-left: 2rem;">
                    <li>Receive automated compliance reports</li>
                    <li>Get ongoing AI recommendations</li>
                    <li>Access audit-ready evidence reports</li>
                    <li>Monitor compliance progress over time</li>
                </ul>
                <a href="/upload" class="btn">🚀 Continue Setup</a>
            </div>
        </div>
    </body>
    </html>
    """)

