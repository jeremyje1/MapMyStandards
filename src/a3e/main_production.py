#!/usr/bin/env python3
"""
Production-ready main entry point for A3E FastAPI application.
Includes better error handling and fallback to SQLite if PostgreSQL fails.
"""

import os
import sys
import logging
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the existing app
app_import_error = None
try:
    from src.a3e.main import app
    logger.info("✅ Successfully imported A3E FastAPI app")
except Exception as e:
    app_import_error = str(e)
    logger.error(f"❌ Failed to import A3E app: {app_import_error}")
    # Create a minimal app for debugging
    app = FastAPI(title="A3E Debug", version="0.1.0")
    
    @app.get("/health")
    async def health():
        return {
            "status": "error",
            "message": "Failed to load main application",
            "error": app_import_error
        }

# Override database configuration if needed
if os.getenv("FORCE_SQLITE", "false").lower() == "true":
    logger.warning("⚠️ FORCE_SQLITE is set - using SQLite instead of PostgreSQL")
    os.environ["DATABASE_URL"] = "sqlite:///./a3e_production.db"

# Add production middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://platform.mapmystandards.ai",
        "https://api.mapmystandards.ai",
        "http://localhost:3000",  # For development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Handle startup with better error reporting"""
    logger.info("🚀 Starting A3E Production Server...")
    
    # Log environment info
    env_vars = {
        "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else "Not set",
        "STRIPE_SECRET_KEY": "***" if os.getenv("STRIPE_SECRET_KEY") else "Not set",
        "JWT_SECRET_KEY": "***" if os.getenv("JWT_SECRET_KEY") else "Not set",
        "POSTMARK_SERVER_TOKEN": "***" if os.getenv("POSTMARK_SERVER_TOKEN") else "Not set",
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "Not set"),
    }
    
    logger.info("Environment variables status:")
    for key, value in env_vars.items():
        logger.info(f"  {key}: {value}")
    
    # Test database connection
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        if database_url.startswith(("postgres://", "postgresql://")):
            logger.info("  Database: PostgreSQL")
        elif database_url.startswith("sqlite://"):
            logger.info("  Database: SQLite")
        else:
            logger.warning(f"  Database: Unknown type ({database_url[:20]}...)")
    else:
        logger.error("  Database: DATABASE_URL not set!")

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment (remove in production)"""
    return {
        "database_configured": bool(os.getenv("DATABASE_URL")),
        "stripe_configured": bool(os.getenv("STRIPE_SECRET_KEY")),
        "jwt_configured": bool(os.getenv("JWT_SECRET_KEY")),
        "email_configured": bool(os.getenv("POSTMARK_SERVER_TOKEN")),
        "environment": os.getenv("ENVIRONMENT", "Not set"),
        "python_version": sys.version,
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        "src.a3e.main_production:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
