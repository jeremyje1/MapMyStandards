#!/bin/bash

# MapMyStandards Unified Deployment Script
# Usage: ./scripts/deploy.sh [dev|staging|production]

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 MapMyStandards Deployment Script${NC}"
echo -e "${YELLOW}Environment: ${ENVIRONMENT}${NC}"

# Function to check requirements
check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is required but not installed.${NC}"
        exit 1
    fi
    
    # Check Node
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is required but not installed.${NC}"
        exit 1
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}No .env file found. Creating from template...${NC}"
        cp .env.example .env
        echo -e "${RED}Please configure .env file and run again.${NC}"
        exit 1
    fi
}

# Development deployment
deploy_dev() {
    echo -e "${GREEN}Starting development deployment...${NC}"
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    
    # Install Node dependencies
    echo "Installing Node dependencies..."
    npm install
    
    # Build frontend
    echo "Building frontend..."
    npm run build
    
    # Initialize database
    echo "Initializing database..."
    python3 -c "from src.a3e.database.connection import init_db; init_db()"
    
    # Start services
    echo -e "${GREEN}Starting development servers...${NC}"
    # Start FastAPI in background
    uvicorn src.a3e.main:app --reload --host 0.0.0.0 --port 8000 &
    # Start Next.js
    npm run dev
}

# Staging deployment
deploy_staging() {
    echo -e "${GREEN}Starting staging deployment...${NC}"
    
    # Build and test
    echo "Running tests..."
    pytest tests/ || true
    
    # Build production assets
    echo "Building production assets..."
    npm run build
    
    # Build Docker image
    echo "Building Docker image..."
    docker build -t mapmystandards:staging .
    
    # Run migrations
    echo "Running database migrations..."
    alembic upgrade head
    
    # Start with Docker
    echo "Starting staging environment..."
    docker run -d \
        --name mapmystandards-staging \
        --env-file .env \
        -p 8000:8000 \
        mapmystandards:staging
}

# Production deployment
deploy_production() {
    echo -e "${GREEN}Starting production deployment...${NC}"
    
    # Confirm production deployment
    echo -e "${YELLOW}⚠️  You are about to deploy to PRODUCTION!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "Deployment cancelled."
        exit 0
    fi
    
    # Run all tests
    echo "Running full test suite..."
    pytest tests/ --cov --cov-report=term-missing
    
    # Build production bundle
    echo "Building production bundle..."
    npm run build
    npm run tailwind:build
    
    # Build and push Docker image
    echo "Building production Docker image..."
    docker build -t mapmystandards:production -f Dockerfile.production .
    
    # Deploy to Railway/Vercel
    if command -v railway &> /dev/null; then
        echo "Deploying to Railway..."
        railway up
    elif command -v vercel &> /dev/null; then
        echo "Deploying to Vercel..."
        vercel --prod
    else
        echo -e "${YELLOW}No deployment platform detected. Using Docker locally.${NC}"
        docker run -d \
            --name mapmystandards-production \
            --env-file .env.production \
            -p 80:8000 \
            --restart unless-stopped \
            mapmystandards:production
    fi
    
    echo -e "${GREEN}✅ Production deployment complete!${NC}"
}

# Main execution
check_requirements

case $ENVIRONMENT in
    dev|development)
        deploy_dev
        ;;
    staging|stage)
        deploy_staging
        ;;
    production|prod)
        deploy_production
        ;;
    *)
        echo -e "${RED}Invalid environment: ${ENVIRONMENT}${NC}"
        echo "Usage: ./scripts/deploy.sh [dev|staging|production]"
        exit 1
        ;;
esac