"""
CORS Configuration for FastAPI
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

def configure_cors(app: FastAPI):
    """Configure CORS middleware for the FastAPI application"""
    
    # Define allowed origins
    allowed_origins = [
        "https://mapmystandards.ai",
        "https://www.mapmystandards.ai",
        "https://api.mapmystandards.ai",
        "https://platform.mapmystandards.ai",
    ]
    
    # Add localhost for development if not in production
    if os.getenv("ENVIRONMENT", "development") != "production":
        allowed_origins.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ])
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,  # Required for cookies
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],  # Can be more restrictive in production
        expose_headers=["Content-Range", "X-Total-Count"],  # For pagination
        max_age=3600,  # Cache preflight requests for 1 hour
    )
    
    return app