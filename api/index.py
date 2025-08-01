"""
Lightweight entry point for Vercel deployment
This reduces the initial bundle size by importing the main app dynamically
"""
import os
import sys

# Add the source directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main FastAPI app
try:
    from platform_demo import app
except ImportError as e:
    # Fallback minimal app if import fails
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="MapMyStandards.ai", version="1.0.0")
    
    @app.get("/")
    async def root():
        return JSONResponse({
            "status": "error",
            "message": f"Import error: {str(e)}",
            "service": "MapMyStandards.ai"
        })
    
    @app.get("/health")
    async def health():
        return JSONResponse({"status": "error", "import_error": str(e)})

# Expose the app for Vercel
handler = app
