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