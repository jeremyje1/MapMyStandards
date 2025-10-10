#!/bin/bash

# A³E Production Deployment Script
# 
# This script deploys the A³E system to production using Docker Compose

set -e

echo "🚀 A³E Production Deployment"
echo "============================"

wait_for() {
    local description="$1"
    local max_attempts="$2"
    local sleep_seconds="$3"
    shift 3

    echo "Waiting for ${description}..."
    local attempt=1
    while [ "${attempt}" -le "${max_attempts}" ]; do
        set +e
        "$@"
        local status=$?
        set -e
        if [ ${status} -eq 0 ]; then
            echo "✅ ${description} is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep "${sleep_seconds}"
    done

    echo "❌ ${description} did not become ready after ${max_attempts} attempts."
    return 1
}

# Check if required environment file exists
if [[ ! -f ".env.production" ]]; then
    echo "❌ Error: .env.production file not found!"
    echo "Please create .env.production with all required environment variables."
    echo "Use .env.example as a template."
    exit 1
fi

# Load production environment
source .env.production

echo "📋 Pre-deployment checks..."

# Check Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Check required environment variables
REQUIRED_VARS=(
    "POSTGRES_PASSWORD"
    "REDIS_PASSWORD"
    "SECRET_KEY"
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "OPENAI_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Required environment variables are set"

# Create SSL certificates directory if it doesn't exist
mkdir -p docker/nginx/ssl

# Check if SSL certificates exist
if [[ ! -f "docker/nginx/ssl/cert.pem" ]] || [[ ! -f "docker/nginx/ssl/key.pem" ]]; then
    echo "⚠️  SSL certificates not found. Generating self-signed certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout docker/nginx/ssl/key.pem \
        -out docker/nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=a3e.local"
    echo "✅ Self-signed SSL certificates generated"
fi

# Create static directory for nginx
mkdir -p static

echo "🔧 Building and starting services..."

# Stop any existing containers
docker-compose -f docker-compose.production.yml down

# Build and start all services
docker-compose -f docker-compose.production.yml up -d --build

echo "⏳ Waiting for services to be ready..."

wait_for "PostgreSQL" 30 2 docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U "${POSTGRES_USER:-a3e}"
wait_for "A³E API" 24 5 bash -c 'docker-compose -f docker-compose.production.yml exec -T api python -c "import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")"'

echo "🎉 Deployment complete!"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.production.yml ps

echo ""
echo "🌐 Access Points:"
echo "  • A³E Application: https://localhost"
echo "  • API Documentation: https://localhost/docs"
echo "  • Health Check: https://localhost/health"
echo ""
echo "📝 Next steps:"
echo "  1. Configure your domain name and update SSL certificates"
echo "  2. Set up monitoring and alerting"
echo "  3. Configure backup procedures"
echo "  4. Review and update environment variables for your specific setup"
echo ""
echo "🔧 Management commands:"
echo "  • View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "  • Stop services: docker-compose -f docker-compose.production.yml down"
echo "  • Restart services: docker-compose -f docker-compose.production.yml restart"
