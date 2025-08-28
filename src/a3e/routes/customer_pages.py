"""
Customer-facing page routes
Handles navigation and static pages for the platform
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pages"])

# Get web directory path
WEB_DIR = Path(__file__).resolve().parent.parent.parent.parent / "web"

# Local frontend health endpoint (duplicate logic to ensure it isn't shadowed by the catch-all).
# This ensures deployments depending on /health/frontend don't fail if router ordering or precedence changes.
@router.get("/health/frontend", include_in_schema=False)
async def frontend_health_inline():
    css_path = WEB_DIR / "static" / "css" / "tailwind.css"
    logo_candidates = [
        WEB_DIR / "static" / "img" / "logo.png",
        WEB_DIR / "static" / "img" / "logo.svg",
        WEB_DIR / "static" / "img" / "logo-dark.png",
    ]
    core_js = WEB_DIR / "js" / "a3e-sdk.js"

    def assess(path: Path, name: str, min_bytes: int) -> dict:
        exists = path.exists()
        size = path.stat().st_size if exists else None
        status = "healthy" if exists and size and size >= min_bytes else ("degraded" if exists else "missing")
        return {
            "name": name,
            "path": str(path),
            "exists": exists,
            "size_bytes": size,
            "min_threshold": min_bytes,
            "status": status,
        }

    assets = [assess(css_path, "tailwind.css", 5000)]
    for lc in logo_candidates:
        if lc.exists():
            assets.append(assess(lc, lc.name, 500))
            break
    assets.append(assess(core_js, "a3e-sdk.js", 200))
    overall = "healthy"
    if any(a["status"] == "missing" for a in assets):
        overall = "missing"
    elif any(a["status"] == "degraded" for a in assets):
        overall = "degraded"
    return {"status": overall, "assets": assets}

def serve_html_file(filename: str, fallback: str = None):
    """Serve an HTML file from the web directory"""
    file_path = WEB_DIR / filename
    if file_path.exists():
        return FileResponse(str(file_path))
    elif fallback:
        fallback_path = WEB_DIR / fallback
        if fallback_path.exists():
            return FileResponse(str(fallback_path))
    raise HTTPException(status_code=404, detail=f"Page not found: {filename}")

@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page():
    """Login page"""
    return serve_html_file("login.html")

@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page():
    """Dashboard page placeholder redirect until unified dashboard available."""
    try:
        return serve_html_file("dashboard.html")
    except HTTPException:
        return RedirectResponse(url="/upload")

@router.get("/trial-signup", response_class=HTMLResponse, include_in_schema=False)
async def trial_signup_page():
    """Trial signup page"""
    return serve_html_file("trial-signup.html", fallback="landing.html")

@router.get("/trial-signup.html", response_class=HTMLResponse, include_in_schema=False)
async def trial_signup_html_redirect(request: Request):
    """Redirect /trial-signup.html to /trial-signup preserving query parameters"""
    query_string = str(request.url.query) if request.url.query else ""
    redirect_url = "/trial-signup"
    if query_string:
        redirect_url += f"?{query_string}"
    return RedirectResponse(url=redirect_url, status_code=301)

@router.get("/trial-success", response_class=HTMLResponse, include_in_schema=False)
async def trial_success_page():
    """Trial success page"""
    return serve_html_file("trial-success.html", fallback="landing.html")

@router.get("/trial-success.html", response_class=HTMLResponse, include_in_schema=False)
async def trial_success_html_redirect(request: Request):
    """Redirect /trial-success.html to /trial-success preserving query parameters"""
    query_string = str(request.url.query) if request.url.query else ""
    redirect_url = "/trial-success"
    if query_string:
        redirect_url += f"?{query_string}"
    return RedirectResponse(url=redirect_url, status_code=301)

@router.get("/pricing", response_class=HTMLResponse, include_in_schema=False)
async def pricing_page():
    """Pricing page"""
    return serve_html_file("pricing.html", fallback="landing.html")

@router.get("/features", response_class=HTMLResponse, include_in_schema=False)
async def features_page():
    """Features page"""
    return serve_html_file("features.html")

@router.get("/about", response_class=HTMLResponse, include_in_schema=False)
async def about_page():
    """About page"""
    return serve_html_file("about.html")

@router.get("/contact", response_class=HTMLResponse, include_in_schema=False)
async def contact_page():
    """Contact page"""
    return serve_html_file("contact.html")

@router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_page():
    """Privacy policy page"""
    return serve_html_file("privacy.html")

@router.get("/docs", response_class=HTMLResponse, include_in_schema=False)
async def docs_redirect():
    """Redirect /docs to actual API docs"""
    return RedirectResponse(url="/redoc")

@router.get("/upload", response_class=HTMLResponse, include_in_schema=False)
async def upload_page():
    """Evidence upload page"""
    return serve_html_file("upload.html")

@router.get("/onboarding", response_class=HTMLResponse, include_in_schema=False)
async def onboarding_page():
    """Onboarding page"""
    return serve_html_file("onboarding.html", fallback="dashboard.html")

@router.get("/standards", response_class=HTMLResponse, include_in_schema=False)
async def standards_page():
    """Standards page"""
    return serve_html_file("standards.html")

@router.get("/reports", response_class=HTMLResponse, include_in_schema=False)
async def reports_page():
    """Reports page"""
    return serve_html_file("reports.html")

@router.get("/services", response_class=HTMLResponse, include_in_schema=False) 
async def services_page():
    """Services page"""
    return serve_html_file("services.html", fallback="features.html")

@router.get("/manual", response_class=HTMLResponse, include_in_schema=False)
async def manual_page():
    """User manual page"""
    return serve_html_file("manual.html")


# Catch-all for missing pages (excluding API routes and health endpoints)
@router.get("/{path:path}", response_class=HTMLResponse, include_in_schema=False)
async def catch_all(path: str):
    """Catch-all route for undefined pages"""
    # Don't handle API routes, health checks, or other system endpoints
    if path.startswith(('api/', 'docs', 'redoc', 'openapi')) or path in ('health', 'health/frontend'):
        # Let these fall through to be handled by other routes
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    
    # Try to find an HTML file with that name
    try:
        return serve_html_file(f"{path}.html")
    except:
        # Check if it's a known redirect
        redirects = {
            "signup": "/trial-signup",
            "register": "/trial-signup",
            "signin": "/login",
            "home": "/",
            "index": "/",
        }
        
        if path.lower() in redirects:
            return RedirectResponse(url=redirects[path.lower()])
        
        # Return a nice 404 page
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Page Not Found - MapMyStandards A³E</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                        background: #f3f4f6;
                    }}
                    .error-container {{
                        text-align: center;
                        padding: 2rem;
                    }}
                    h1 {{ color: #1e3c72; margin-bottom: 1rem; }}
                    p {{ color: #6b7280; margin-bottom: 2rem; }}
                    a {{
                        display: inline-block;
                        padding: 0.75rem 1.5rem;
                        background: #10b981;
                        color: white;
                        text-decoration: none;
                        border-radius: 6px;
                        font-weight: 600;
                    }}
                    a:hover {{
                        background: #059669;
                    }}
                </style>
            </head>
            <body>
                <div class="error-container">
                    <h1>404 - Page Not Found</h1>
                    <p>Sorry, we couldn't find the page "{path}" you're looking for.</p>
                    <a href="/">Return to Homepage</a>
                </div>
            </body>
            </html>
            """,
            status_code=404
        )
