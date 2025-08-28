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

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting test FastAPI application...")
    uvicorn.run(app, host="0.0.0.0", port=8080)