#!/usr/bin/env bash
"""
Complete Domain Setup Script for A3E

Combines NGINX setup and SSL certificate installation for api.mapmystandards.ai
"""

set -e

# Load environment variables
source .env

# Configuration
DOMAIN="api.mapmystandards.ai"
EC2_USER="ubuntu"
SSH_KEY_PATH="~/.ssh/id_rsa"

echo "🌐 Complete Domain Setup for A3E"
echo "🎯 Domain: $DOMAIN"
echo "📍 Target: $EC2_HOST ($EC2_INSTANCE_ID)"
echo ""

# Step 1: Deploy application if not already done
echo "📋 Step 1: Ensuring A3E application is deployed..."
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "test -d /home/$EC2_USER/a3e"; then
    echo "🚀 A3E not found on EC2. Deploying..."
    ./scripts/deploy_ec2.sh
else
    echo "✅ A3E application found on EC2"
    # Ensure it's running
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "cd /home/$EC2_USER/a3e && sudo docker-compose up -d"
fi

# Step 2: Configure NGINX
echo ""
echo "📋 Step 2: Configuring NGINX reverse proxy..."
./scripts/setup_nginx.sh

# Step 3: Wait for DNS propagation check
echo ""
echo "📋 Step 3: DNS Configuration Check"
echo "⚠️  IMPORTANT: Ensure DNS is configured before SSL setup"
echo ""
echo "DNS Requirements:"
echo "  Type: A Record"
echo "  Name: api.mapmystandards.ai"
echo "  Value: $EC2_HOST"
echo "  TTL: 300 (5 minutes)"
echo ""

# Check DNS
echo "🔍 Checking current DNS resolution..."
if command -v dig > /dev/null; then
    RESOLVED_IP=$(dig +short "$DOMAIN" | head -n1)
    if [ "$RESOLVED_IP" = "$EC2_HOST" ]; then
        echo "✅ DNS is correctly configured: $DOMAIN → $EC2_HOST"
        DNS_READY=true
    else
        echo "⚠️  DNS not ready: $DOMAIN → $RESOLVED_IP (expected: $EC2_HOST)"
        DNS_READY=false
    fi
else
    echo "⚠️  dig command not available. Please verify DNS manually."
    DNS_READY=false
fi

if [ "$DNS_READY" = false ]; then
    echo ""
    echo "🕐 DNS Propagation Notice:"
    echo "DNS changes can take 5-60 minutes to propagate globally."
    echo "You can check DNS status with:"
    echo "  nslookup $DOMAIN"
    echo "  dig $DOMAIN"
    echo ""
    read -p "Continue with SSL setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "💡 You can run SSL setup later with: ./scripts/setup_ssl.sh"
        exit 0
    fi
fi

# Step 4: Setup SSL
echo ""
echo "📋 Step 4: Setting up SSL certificate..."
./scripts/setup_ssl.sh

echo ""
echo "🎉 Complete domain setup finished!"
echo ""
echo "🌐 Your A3E API is now live at:"
echo "  https://$DOMAIN"
echo ""
echo "📚 Available endpoints:"
echo "  • Documentation: https://$DOMAIN/docs"
echo "  • Health Check: https://$DOMAIN/health"
echo "  • Institutions: https://$DOMAIN/api/v1/institutions"
echo "  • Standards: https://$DOMAIN/api/v1/standards"
echo "  • Evidence: https://$DOMAIN/api/v1/evidence"
echo "  • Workflows: https://$DOMAIN/api/v1/workflows"
echo ""
echo "🧪 Quick test commands:"
echo "curl https://$DOMAIN/health"
echo "curl https://$DOMAIN/api/v1/institution-types"
echo ""
echo "🎯 Ready for production use!"
