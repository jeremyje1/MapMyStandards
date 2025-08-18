#!/usr/bin/env bash
"""
NGINX Domain Configuration Script for A3E

Configures NGINX reverse proxy with SSL for api.mapmystandards.ai
"""

set -e

# Load environment variables
source .env

# Configuration
DOMAIN="api.mapmystandards.ai"
EC2_USER="ubuntu"
SSH_KEY_PATH="~/.ssh/id_rsa"
NGINX_SITE_CONFIG="/etc/nginx/sites-available/api"
NGINX_SITE_ENABLED="/etc/nginx/sites-enabled/api"

# Function to run commands on EC2
run_remote() {
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$1"
}

#!/bin/bash

# NGINX Setup Script for A³E API (api.mapmystandards.ai)
# Sets up reverse proxy for FastAPI application

set -e

echo "🌐 Setting up NGINX for A³E API"
echo "================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install NGINX if not already installed
if ! command -v nginx &> /dev/null; then
    echo "📦 Installing NGINX..."
    apt update
    apt install -y nginx
    systemctl enable nginx
fi

echo "⚙️  Creating NGINX configuration for api.mapmystandards.ai..."

# Create NGINX configuration for A³E API
cat > /etc/nginx/sites-available/api << 'EOF'
server {
    listen 80;
    server_name api.mapmystandards.ai;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;

    # Client max body size for file uploads
    client_max_body_size 100M;

    # Main API proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed for real-time features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (bypass proxy for faster response)
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /var/www/a3e/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security: deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

echo "🔗 Enabling NGINX site..."

# Remove default site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Enable the A³E API site
ln -sf /etc/nginx/sites-available/api /etc/nginx/sites-enabled/

echo "🧪 Testing NGINX configuration..."
if nginx -t; then
    echo "✅ NGINX configuration valid"
    
    echo "� Reloading NGINX..."
    systemctl reload nginx
    
    echo "✅ NGINX setup complete!"
    echo ""
    echo "📋 Next steps:"
    echo "1. Ensure your FastAPI app is running on port 8000:"
    echo "   cd /path/to/MapMyStandards"
    echo "   gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.a3e.main:app -b 127.0.0.1:8000"
    echo ""
    echo "2. Set up SSL with Let's Encrypt:"
    echo "   sudo ./scripts/setup_ssl.sh"
    echo ""
    echo "3. Test the API:"
    echo "   curl http://api.mapmystandards.ai/"
    
else
    echo "❌ NGINX configuration test failed"
    exit 1
fi

# Test SSH connection
echo "🔗 Testing SSH connection..."
if ! run_remote "echo 'SSH connection successful'"; then
    echo "❌ SSH connection failed. Please check your SSH configuration."
    exit 1
fi

echo "📦 Installing NGINX and Certbot..."
run_remote "sudo apt-get update"
run_remote "sudo apt-get install -y nginx certbot python3-certbot-nginx"

echo "🔧 Creating NGINX site configuration..."
run_remote "sudo tee $NGINX_SITE_CONFIG > /dev/null << 'EOF'
server {
    listen 80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection \"1; mode=block\";
    add_header Referrer-Policy \"strict-origin-when-cross-origin\";
    
    # Client max body size for file uploads
    client_max_body_size 100M;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=upload_limit:10m rate=2r/s;
    
    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # File upload endpoints (with stricter rate limiting)
    location /api/v1/evidence/upload {
        limit_req zone=upload_limit burst=5 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Extended timeouts for file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Health check and documentation
    location ~ ^/(health|docs|redoc) {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Root endpoint
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Access logs
    access_log /var/log/nginx/api_mapmystandards_access.log;
    error_log /var/log/nginx/api_mapmystandards_error.log;
}
EOF"

echo "🔗 Enabling NGINX site..."
run_remote "sudo ln -sf $NGINX_SITE_CONFIG $NGINX_SITE_ENABLED"

echo "✅ Testing NGINX configuration..."
if run_remote "sudo nginx -t"; then
    echo "✅ NGINX configuration is valid"
else
    echo "❌ NGINX configuration test failed"
    exit 1
fi

echo "🔄 Restarting NGINX..."
run_remote "sudo systemctl restart nginx"
run_remote "sudo systemctl enable nginx"

echo "🔍 Checking if A3E application is running..."
if run_remote "curl -f http://localhost:8000/health"; then
    echo "✅ A3E application is running"
else
    echo "⚠️  A3E application is not responding. Starting it..."
    run_remote "cd /home/$EC2_USER/a3e && sudo docker-compose up -d"
    sleep 10
    
    if run_remote "curl -f http://localhost:8000/health"; then
        echo "✅ A3E application started successfully"
    else
        echo "❌ A3E application failed to start. Check logs:"
        run_remote "cd /home/$EC2_USER/a3e && sudo docker-compose logs --tail=20"
        exit 1
    fi
fi

echo "🌐 Testing HTTP access..."
if run_remote "curl -f http://localhost/health"; then
    echo "✅ NGINX reverse proxy is working"
else
    echo "❌ NGINX reverse proxy test failed"
    exit 1
fi

echo ""
echo "🎉 NGINX reverse proxy configured successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Ensure DNS: $DOMAIN → $EC2_HOST"
echo "2. Test HTTP: http://$DOMAIN/health"
echo "3. Install SSL: ./scripts/setup_ssl.sh"
echo ""
echo "Manual SSL setup:"
echo "  ssh -i $SSH_KEY_PATH $EC2_USER@$EC2_HOST"
echo "  sudo certbot --nginx -d $DOMAIN"
echo ""
echo "🔗 Access URLs:"
echo "  HTTP: http://$DOMAIN"
echo "  API Docs: http://$DOMAIN/docs"
echo "  Health Check: http://$DOMAIN/health"
