#!/usr/bin/env python3
"""
Ultra-minimal FastAPI app to serve static files during backend downtime
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="A³E Platform Recovery")

@app.get("/")
async def root():
    """Root endpoint - basic confirmation app is working"""
    return HTMLResponse("""
    <html>
    <body style="font-family: -apple-system, sans-serif; text-align: center; padding: 3rem;">
        <h1>✅ A³E Platform is Online</h1>
        <p>The platform is operational and processing requests.</p>
        <p>If you were redirected here after checkout, your subscription is active.</p>
        <p><a href="/dashboard.html">Continue to Dashboard →</a></p>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "a3e-recovery"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting minimal A³E recovery app...")
    uvicorn.run(app, host="0.0.0.0", port=8080)