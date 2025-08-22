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

###############################################
# Frontend (Tailwind CSS) build stage
###############################################
FROM node:20-alpine AS assets
WORKDIR /webapp
# Only copy web package manifest first for better caching
COPY web/package.json ./web/package.json
WORKDIR /webapp/web
RUN npm install --no-audit --no-fund
# Copy the remainder of the web directory (Tailwind input + config + any src)
COPY web/ ./
# Build Tailwind CSS (outputs to web/static/css/tailwind.css)
RUN npm run build-css

###############################################
# Back to base python image for application
###############################################
WORKDIR /app

# Copy application source
COPY . .
# Copy built CSS artifact from assets stage (ensure directory exists)
COPY --from=assets /webapp/web/static/css/tailwind.css web/static/css/tailwind.css

# Make startup script executable
RUN chmod +x start.sh

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose (optional – Railway sets $PORT)
EXPOSE 8000

# Simple healthcheck (login page is public GET)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD sh -c 'curl -fsS http://127.0.0.1:${PORT:-8000}/health || exit 1'

# Use startup script
CMD ["./start.sh"]
