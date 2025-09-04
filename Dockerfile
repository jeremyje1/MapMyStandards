# Use Python 3.9 slim image for faster builds
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements*.txt ./

# Use production requirements for Railway deployment
RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements-production.txt ]; then \
        pip install --no-cache-dir -r requirements-production.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy the application code
COPY . .

# Expose the port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Make start script executable if it exists
RUN if [ -f /app/start.sh ]; then chmod +x /app/start.sh; fi

# Command to run the application with better error handling
CMD ["sh", "-c", "python -m uvicorn src.a3e.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info || (echo 'Failed to start uvicorn'; exit 1)"]
