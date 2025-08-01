#!/usr/bin/env python3
"""
Minimal test API to debug Railway deployment
"""

from fastapi import FastAPI
import uvicorn
import os

# Create minimal app
app = FastAPI(title="Test API")

@app.get("/")
def root():
    return {"status": "working", "message": "Minimal test API is running"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": "test"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting test API on port {port}")
    uvicorn.run(
        "minimal_test_api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
