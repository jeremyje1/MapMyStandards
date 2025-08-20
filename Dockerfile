# Python slim base image
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system deps needed for bcrypt/passlib and runtime utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose (optional – Railway sets $PORT)
EXPOSE 8000

# Simple healthcheck (login page is public GET)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8000}/login || exit 1

# Use uvicorn directly for FastAPI
CMD uvicorn src.a3e.main:app --host 0.0.0.0 --port ${PORT:-8000}
