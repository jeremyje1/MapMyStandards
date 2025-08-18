#!/usr/bin/env python3
"""
Ultra-minimal API for Railway debugging
"""

from fastapi import FastAPI
import uvicorn
import os

# Absolutely minimal FastAPI app
app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok", "message": "ultra minimal API working"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"Starting ultra-minimal API on port {port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
