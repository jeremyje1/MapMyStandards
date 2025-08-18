"""
Minimal FastAPI app for testing web routes
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI(title="A3E Landing Page Test")

# Web routes for mapmystandards.ai integration
@app.get("/landing", response_class=HTMLResponse, include_in_schema=False)
async def landing_page(request: Request):
    """Landing page for mapmystandards.ai integration."""
    try:
        with open("web/landing.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Landing page not found</h1>", status_code=404)

@app.get("/checkout", response_class=HTMLResponse, include_in_schema=False)
async def checkout_page(request: Request):
    """Checkout page for subscription signup."""
    try:
        with open("web/checkout.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Checkout page not found</h1>", status_code=404)

# Mount static files for web assets
app.mount("/web", StaticFiles(directory="web"), name="web")

@app.get("/")
async def root():
    return {"message": "A3E Web Integration Test", "landing": "/landing", "checkout": "/checkout"}

# Minimal API endpoints for testing
@app.post("/api/trial-signup")
async def trial_signup():
    """Mock trial signup endpoint."""
    return {
        "success": True,
        "message": "Trial signup successful",
        "api_key": "demo_key_123abc",
        "trial_days": 14
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "A3E Web Integration"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
