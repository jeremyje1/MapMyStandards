"""URL helper utilities for building public platform and API URLs.

Centralizes construction so tests, templates, and email services can avoid
hard-coding production domains. Falls back to settings defaults.
"""

from __future__ import annotations

from .config import settings
from typing import Optional


def _join(base: str, path: str) -> str:
    if not path:
        return base.rstrip('/')
    if path.startswith('http://') or path.startswith('https://'):
        return path  # already absolute
    if not path.startswith('/'):
        path = '/' + path
    return base.rstrip('/') + path


def public_app_url(path: str = "") -> str:
    """Return full public application (frontend) URL for a path."""
    return _join(settings.PUBLIC_APP_URL, path)


def public_api_url(path: str = "") -> str:
    """Return full public API URL for a path."""
    return _join(settings.PUBLIC_API_URL, path)

def build_unsubscribe_link(token: Optional[str] = None) -> str:
    """Return unsubscribe/preferences link with optional token."""
    base = public_app_url("/email-preferences")
    if token:
        return f"{base}?token={token}"
    return base


__all__ = ["public_app_url", "public_api_url", "build_unsubscribe_link"]
