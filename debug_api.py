#!/usr/bin/env python3
"""
Debug API to understand Railway health check behavior
"""

from fastapi import FastAPI
import uvicorn
import os
import time
import logging

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Log every detail during startup
logger.info("🚀 Starting FastAPI app initialization...")

@app.get("/")
def root():
    logger.info("📍 Root endpoint accessed")
    return {"status": "ok", "message": "debug API working", "timestamp": time.time()}

@app.get("/health")
def health():
    logger.info("❤️ Health endpoint accessed")
    return {"status": "healthy", "timestamp": time.time()}

@app.on_event("startup")
async def startup_event():
    logger.info("🎯 FastAPI startup event triggered")

@app.on_event("shutdown") 
async def shutdown_event():
    logger.info("🛑 FastAPI shutdown event triggered")

if __name__ == "__main__":
    logger.info("🔧 Starting uvicorn server setup...")
    
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🌐 Port configured: {port}")
    
    logger.info("📡 Environment variables:")
    for key, value in os.environ.items():
        if 'PORT' in key or 'HOST' in key:
            logger.info(f"   {key}={value}")
    
    logger.info("🚀 Calling uvicorn.run...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="debug"
    )
