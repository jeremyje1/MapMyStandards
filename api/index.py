"""
Lightweight entry point for Vercel deployment
This reduces the initial bundle size by importing the main app dynamically
"""
import os
import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Add the source directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create the main app
app = FastAPI(title="MapMyStandards.ai", version="1.0.0")

@app.get("/")
async def root():
    try:
        # Test if we can import the main platform
        from platform_demo import app as main_app
        return JSONResponse({
            "status": "success",
            "message": "MapMyStandards.ai is running",
            "service": "MapMyStandards.ai",
            "import_status": "main app imported successfully"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error", 
            "message": f"Import error: {str(e)}",
            "service": "MapMyStandards.ai",
            "python_path": sys.path[:3],
            "working_dir": os.getcwd(),
            "files_in_dir": os.listdir(".")[:10]
        })

@app.get("/health")
async def health():
    return JSONResponse({
        "status": "healthy",
        "service": "MapMyStandards.ai",
        "environment": "production"
    })

@app.get("/test")
async def test():
    try:
        # Import and mount the full app
        from platform_demo import app as main_app
        
        # Get all routes from main app
        routes = [route.path for route in main_app.routes]
        
        return JSONResponse({
            "status": "success",
            "available_routes": routes[:10],
            "total_routes": len(routes)
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "type": str(type(e).__name__)
        })

# Expose the app for Vercel
handler = app
