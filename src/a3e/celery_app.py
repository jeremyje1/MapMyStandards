"""Celery application bootstrap for A³E background tasks."""
from __future__ import annotations

import os

from celery import Celery


def _redis_url() -> str:
    """Resolve the Redis broker URL for Celery.

    Prefers explicit CELERY_BROKER_URL but falls back to REDIS_URL, matching
    the configuration used by the FastAPI application. Raises a clear error if
    no broker can be determined so deployment failures are easier to diagnose.
    """

    broker = os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL")
    if not broker:
        raise RuntimeError(
            "Celery broker URL is not configured. Set CELERY_BROKER_URL or REDIS_URL."
        )
    return broker


celery_app = Celery(
    "a3e",
    broker=_redis_url(),
    backend=os.getenv("CELERY_RESULT_BACKEND") or os.getenv("REDIS_URL"),
)

# Use JSON serialization by default to avoid requiring pickle in production.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=os.getenv("TZ", "UTC"),
    enable_utc=True,
)


@celery_app.task(name="a3e.healthcheck.ping")
def ping() -> str:
    """Simple built-in task that confirms the worker is alive."""

    return "pong"
