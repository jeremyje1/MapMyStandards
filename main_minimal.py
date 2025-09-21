"""
Minimal version of main.py for debugging deployment issues.
This temporarily disables webhook and workspace features.
"""
import os
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from a3e.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="MapMyStandards API (Minimal)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = [
    "https://platform.mapmystandards.ai",
    "https://api.mapmystandards.ai",
    "https://mapmystandards.ai",
    "https://www.mapmystandards.ai",
    "https://app.mapmystandards.ai",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"CORS configured with origins: {cors_origins}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0-minimal",
        "mode": "debugging"
    }

# Basic info endpoint
@app.get("/")
async def root():
    return {
        "message": "MapMyStandards API (Minimal Mode)",
        "docs": "/docs",
        "health": "/health"
    }

# Import only essential routers
try:
    from a3e.api.routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    logger.info("✅ Auth router loaded")
except Exception as e:
    logger.error(f"❌ Failed to load auth router: {e}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)