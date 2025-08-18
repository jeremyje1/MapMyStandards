"""
Vercel serverless function entry point for MapMyStandards.ai
This imports and serves the main FastAPI application.
"""

import sys
import os

# Add the parent directory to sys.path so we can import platform_demo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import the main FastAPI application
    from platform_demo import app
    
    # For Vercel serverless functions, we need to export the app
    # Vercel expects the ASGI application to be available as 'app'
    
except Exception as e:
    # If import fails, create a fallback app that shows the error
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    import traceback
    
    app = FastAPI(title="MapMyStandards.ai - Error", version="1.0.0")
    
    error_info = {
        "status": "error",
        "message": f"Failed to import main application: {str(e)}",
        "traceback": traceback.format_exc(),
        "sys_path": sys.path,
        "working_directory": os.getcwd(),
        "directory_contents": os.listdir(os.getcwd()) if os.path.exists(os.getcwd()) else "directory not found"
    }
    
    @app.get("/")
    async def error_root():
        return JSONResponse(content=error_info, status_code=500)
    
    @app.get("/error")
    async def error_details():
        return JSONResponse(content=error_info, status_code=500)
