#!/bin/bash

# A³E Quick Deployment Script for VPS
# Usage: curl -sSL https://raw.githubusercontent.com/your-username/MapMyStandards/main/scripts/quick-deploy.sh | bash

set -e

echo "🚀 A³E Quick Deployment Script"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting A³E deployment on VPS..."

# Update system
log_info "Updating system packages..."
apt update && apt upgrade -y

# Install Docker
if ! command -v docker &> /dev/null; then
    log_info "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
else
    log_info "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_info "Installing Docker Compose..."
    apt install docker-compose-plugin -y
else
    log_info "Docker Compose already installed"
fi

# Install Git (if not present)
if ! command -v git &> /dev/null; then
    log_info "Installing Git..."
    apt install git -y
fi

# Create application directory
APP_DIR="/opt/a3e"
log_info "Creating application directory at $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone repository
if [[ ! -d ".git" ]]; then
    log_info "Cloning A³E repository..."
    git clone https://github.com/jeremyje1/MapMyStandards.git .
else
    log_info "Updating existing repository..."
    git pull origin main
fi

# Create production environment file
if [[ ! -f ".env.production" ]]; then
    log_info "Creating production environment file..."
    cp .env.production.example .env.production
    
    # Generate secure secrets
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    
    # Update .env.production with generated secrets
    sed -i "s/your_secure_postgres_password_here/$POSTGRES_PASSWORD/g" .env.production
    sed -i "s/your_32_char_secret_key_here/$SECRET_KEY/g" .env.production
    sed -i "s/your_secure_redis_password_here/$REDIS_PASSWORD/g" .env.production
    
    log_warn "IMPORTANT: Edit .env.production to add your API keys:"
    log_warn "  - OPENAI_API_KEY"
    log_warn "  - CANVAS_ACCESS_TOKEN"
    log_warn "  - Your domain name"
    
    echo
    read -p "Press Enter after you've updated .env.production with your API keys..."
else
    log_info "Using existing .env.production file"
fi

# Create necessary directories
log_info "Creating application directories..."
mkdir -p logs data/postgres data/milvus data/redis docker/nginx/ssl

# Set permissions
log_info "Setting file permissions..."
chmod +x deploy.sh
chmod +x scripts/*.sh 2>/dev/null || true

# Deploy the application
log_info "Deploying A³E application..."
./deploy.sh

# Wait for services to start
log_info "Waiting for services to start..."
sleep 30

# Check health
log_info "Checking application health..."
if curl -s http://localhost:8000/health > /dev/null; then
    log_info "✅ Application is healthy!"
else
    log_warn "Application may still be starting. Check logs with:"
    log_warn "docker-compose -f docker-compose.production.yml logs -f"
fi

# Setup firewall (optional)
read -p "Do you want to configure UFW firewall? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Configuring UFW firewall..."
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    log_info "Firewall configured (SSH, HTTP, HTTPS allowed)"
fi

# Setup SSL (optional)
read -p "Do you have a domain name and want to setup SSL? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain name: " DOMAIN
    if [[ ! -z "$DOMAIN" ]]; then
        log_info "Setting up SSL for $DOMAIN..."
        apt install certbot python3-certbot-nginx -y
        
        # Update nginx config with domain
        sed -i "s/server_name _;/server_name $DOMAIN www.$DOMAIN;/g" docker/nginx/nginx.conf
        
        # Restart nginx
        docker-compose -f docker-compose.production.yml restart nginx
        
        # Get SSL certificate
        certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --register-unsafely-without-email
        
        # Setup auto-renewal
        (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
        
        log_info "SSL configured for $DOMAIN"
    fi
fi

# Final status
echo
echo "🎉 A³E Deployment Complete!"
echo "=========================="
echo
log_info "Your A³E system is now running!"
echo
echo "Access Points:"
echo "  - Application: http://$(curl -s ifconfig.me)"
echo "  - API Docs: http://$(curl -s ifconfig.me)/docs"
echo "  - Health Check: http://$(curl -s ifconfig.me)/health"
echo
echo "Useful Commands:"
echo "  - View logs: docker-compose -f docker-compose.production.yml logs -f"
echo "  - Restart: docker-compose -f docker-compose.production.yml restart"
echo "  - Stop: docker-compose -f docker-compose.production.yml down"
echo "  - Update: git pull && docker-compose -f docker-compose.production.yml up -d --build"
echo
echo "Configuration files:"
echo "  - App directory: $APP_DIR"
echo "  - Environment: $APP_DIR/.env.production"
echo "  - Logs: $APP_DIR/logs/"
echo
log_warn "Remember to:"
log_warn "1. Update your .env.production file with real API keys"
log_warn "2. Point your domain DNS to this server IP: $(curl -s ifconfig.me)"
log_warn "3. Setup monitoring and backups"
log_warn "4. Review security settings"
echo
log_info "Happy deploying! 🚀"
