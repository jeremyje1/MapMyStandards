"""Shared URL constants for tests to avoid hard-coded production domains.

Prefer reading from environment when provided so CI can override.
Falls back to config settings via url_helpers if available.
"""

import os
try:
    from src.a3e.core.url_helpers import public_api_url, public_app_url  # type: ignore
except Exception:  # minimal import fallback if package path differs
    def public_api_url(path: str = ""):
        base = os.getenv("PUBLIC_API_URL", "https://api.mapmystandards.ai")
        return base.rstrip('/') + (path if path.startswith('/') else f"/{path}" if path else "")
    def public_app_url(path: str = ""):
        base = os.getenv("PUBLIC_APP_URL", "https://platform.mapmystandards.ai")
        return base.rstrip('/') + (path if path.startswith('/') else f"/{path}" if path else "")

API_BASE = os.getenv("PUBLIC_API_URL", public_api_url())
APP_BASE = os.getenv("PUBLIC_APP_URL", public_app_url())

__all__ = ["API_BASE", "APP_BASE", "public_api_url", "public_app_url"]
