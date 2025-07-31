#!/bin/bash

# A³E Production Deployment Script
# 
# This script deploys the A³E system to production using Docker Compose

set -e

echo "🚀 A³E Production Deployment"
echo "============================"

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

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
timeout 60 bash -c 'until docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-a3e}; do sleep 2; done'

# Wait for API to be ready
echo "Waiting for A³E API..."
timeout 120 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 5; done'

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
