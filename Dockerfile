###############################################
# Stage 1: Build frontend assets (Tailwind CSS)
###############################################
FROM node:20-alpine AS assets
WORKDIR /web
COPY web/package.json ./package.json
RUN npm install --no-audit --no-fund
COPY web/ .
RUN npm run build-css

###############################################
# Stage 2: Python runtime image
###############################################
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Copy built CSS artifact
COPY --from=assets /web/static/css/tailwind.css web/static/css/tailwind.css

# Ensure startup script executable
RUN chmod +x start.sh

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD sh -c 'curl -fsS http://127.0.0.1:${PORT:-8000}/health || exit 1'

CMD ["./start.sh"]
