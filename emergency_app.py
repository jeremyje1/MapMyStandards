#!/usr/bin/env python3
"""
Emergency minimal app - absolute simplest FastAPI app possible
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/")
def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html><head><title>A³E Platform Online</title></head>
    <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 3rem;">
        <h1>✅ A³E Platform Restored</h1>
        <p>Emergency recovery mode active.</p>
        <p><a href="/dashboard.html">Continue to Dashboard</a></p>
    </body></html>
    """)

@app.get("/dashboard.html")
@app.get("/dashboard")
def dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html><head><title>Welcome to A³E Platform</title>
    <meta http-equiv="refresh" content="2; url=trial-success.html"></head>
    <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 3rem;">
        <div style="width: 60px; height: 60px; background: #10b981; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 2rem;">
            <span style="color: white; font-size: 2rem; font-weight: bold;">✓</span>
        </div>
        <h1>Welcome to A³E Platform!</h1>
        <p>Your subscription is active and ready to use.</p>
        <p>Redirecting you to the platform...</p>
        <p><a href="trial-success.html">Click here if not redirected</a></p>
        <script>
            localStorage.setItem('a3e_subscription_active', 'true');
            setTimeout(() => window.location.href = 'trial-success.html', 2000);
        </script>
    </body></html>
    """)

@app.get("/health")
def health():
    return {"status": "emergency_mode", "service": "a3e"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)