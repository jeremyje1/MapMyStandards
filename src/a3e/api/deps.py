"""Shared dependencies for AI module endpoints."""

from __future__ import annotations

import os
from functools import lru_cache
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import get_settings
from ..database.connection import db_manager

FeatureFlagName = str


@lru_cache(maxsize=None)
def _flag_enabled(flag_name: FeatureFlagName) -> bool:
    value = os.getenv(flag_name, "false").lower()
    return value in {"1", "true", "yes", "on"}


def feature_enabled(flag_name: FeatureFlagName):
    """Ensure a feature flag environment toggle is enabled."""

    def _check() -> bool:
        if _flag_enabled(flag_name):
            return True
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"{flag_name} not enabled",
        )

    return _check


async def get_ai_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an initialized async database session for AI routes."""
    if not db_manager._initialized:  # type: ignore[attr-defined]
        await db_manager.initialize()
    async with db_manager.get_session() as session:
        yield session


def get_ai_settings():
    """Return cached settings (alias to keep imports lightweight)."""
    return get_settings()
