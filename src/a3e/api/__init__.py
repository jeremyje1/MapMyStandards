"""
API package initialization for A3E

Provides the main API router and middleware configuration.
"""

from fastapi import APIRouter
from .routes import api_router

__all__ = ["api_router"]
