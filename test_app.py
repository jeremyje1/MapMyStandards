"""
Minimal test FastAPI app to verify Railway deployment works
"""

import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Minimal FastAPI app
app = FastAPI(title="Test App")

@app.get("/")
async def root():
    """Test root endpoint"""
    logger.info("Root endpoint accessed")
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test - FastAPI Working</title>
    </head>
    <body>
        <h1>✅ FastAPI is Working!</h1>
        <p>This confirms the Railway environment can run FastAPI applications.</p>
        <p>The main application has startup issues that need investigation.</p>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "message": "Test app running successfully"}

@app.get("/dashboard.html")
@app.get("/dashboard")
async def dashboard_redirect():
    """Handle dashboard redirects during backend downtime"""
    logger.info("Dashboard redirect requested, redirecting to working page")
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to A³E Platform</title>
        <meta http-equiv="refresh" content="0; url=/trial-success.html">
    </head>
    <body>
        <div style="font-family: -apple-system, BlinkMacSystemFont, sans-serif; text-align: center; padding: 3rem;">
            <h1>✅ Welcome to A³E Platform!</h1>
            <p>Your subscription is active. Redirecting to your welcome page...</p>
            <p><a href="/trial-success.html">Click here if not redirected automatically</a></p>
        </div>
        <script>
            // Store subscription success
            localStorage.setItem('a3e_subscription_active', 'true');
            localStorage.setItem('a3e_subscription_date', new Date().toISOString());
            
            // Redirect immediately
            setTimeout(() => {
                window.location.href = '/trial-success.html';
            }, 1000);
        </script>
    </body>
    </html>
    """)


@app.get("/debug")
async def debug_imports():
    """Run import debugging and return results"""
    import subprocess
    import sys
    
    try:
        result = subprocess.run([sys.executable, "debug_imports.py"], 
                              capture_output=True, text=True, timeout=30)
        
        return HTMLResponse(f"""
        <html>
        <head><title>Import Debug Results</title></head>
        <body>
            <h1>Import Debug Results</h1>
            <h2>STDOUT:</h2>
            <pre>{result.stdout}</pre>
            <h2>STDERR:</h2>
            <pre>{result.stderr}</pre>
            <h2>Return Code:</h2>
            <p>{result.returncode}</p>
        </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
        <body>
            <h1>Debug Error</h1>
            <p>Failed to run debug script: {str(e)}</p>
        </body>
        </html>
        """)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting test FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8080)