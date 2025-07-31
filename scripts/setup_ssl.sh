#!/usr/bin/env bash
"""
SSL Certificate Setup Script for A3E

Installs and configures SSL certificate for api.mapmystandards.ai using Let's Encrypt
"""

set -e

# Load environment variables
source .env

# Configuration
DOMAIN="api.mapmystandards.ai"
EC2_USER="ubuntu"
SSH_KEY_PATH="~/.ssh/id_rsa"
EMAIL="admin@mapmystandards.ai"  # Update this with your email

# Function to run commands on EC2
run_remote() {
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$1"
}

echo "🔒 Setting up SSL certificate for $DOMAIN..."
echo "📍 Target: $EC2_HOST ($EC2_INSTANCE_ID)"

# Test SSH connection
echo "🔗 Testing SSH connection..."
if ! run_remote "echo 'SSH connection successful'"; then
    echo "❌ SSH connection failed. Please check your SSH configuration."
    exit 1
fi

echo "🌐 Checking DNS resolution..."
if dig +short "$DOMAIN" | grep -q "$EC2_HOST"; then
    echo "✅ DNS is correctly pointing $DOMAIN → $EC2_HOST"
else
    echo "⚠️  DNS Warning: $DOMAIN may not be pointing to $EC2_HOST"
    echo "Please ensure your DNS records are configured correctly:"
    echo "  Type: A"
    echo "  Name: api.mapmystandards.ai"
    echo "  Value: $EC2_HOST"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔍 Testing HTTP access..."
if curl -f "http://$DOMAIN/health" > /dev/null 2>&1; then
    echo "✅ HTTP access is working"
else
    echo "❌ HTTP access failed. Please run setup_nginx.sh first"
    exit 1
fi

echo "📦 Ensuring Certbot is installed..."
run_remote "sudo apt-get update && sudo apt-get install -y certbot python3-certbot-nginx"

echo "🔒 Obtaining SSL certificate..."
echo "📧 Using email: $EMAIL"

# Run certbot with automatic nginx configuration
run_remote "sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect"

echo "✅ Testing SSL certificate..."
if curl -f "https://$DOMAIN/health" > /dev/null 2>&1; then
    echo "✅ HTTPS is working correctly!"
else
    echo "❌ HTTPS test failed. Checking NGINX configuration..."
    run_remote "sudo nginx -t"
    run_remote "sudo systemctl status nginx"
fi

echo "🔄 Setting up automatic renewal..."
run_remote "sudo systemctl enable certbot.timer"
run_remote "sudo systemctl start certbot.timer"

echo "🧪 Testing certificate renewal..."
run_remote "sudo certbot renew --dry-run"

echo "🔍 Checking certificate details..."
run_remote "sudo certbot certificates"

echo ""
echo "🎉 SSL certificate setup complete!"
echo ""
echo "🔗 Your A3E API is now live with HTTPS:"
echo "  🌐 API Base: https://$DOMAIN"
echo "  📚 Documentation: https://$DOMAIN/docs"
echo "  ❤️  Health Check: https://$DOMAIN/health"
echo "  🤖 Bedrock Test: https://$DOMAIN/api/v1/workflows"
echo ""
echo "🔒 Certificate Details:"
echo "  Domain: $DOMAIN"
echo "  Issuer: Let's Encrypt"
echo "  Auto-renewal: Enabled"
echo ""
echo "🛡️  Security Features:"
echo "  ✅ HTTPS/TLS encryption"
echo "  ✅ Automatic HTTP → HTTPS redirect"
echo "  ✅ Security headers (XSS, CSRF protection)"
echo "  ✅ Rate limiting (10 req/s API, 2 req/s uploads)"
echo "  ✅ 100MB file upload limit"
echo ""
echo "📋 Next Steps:"
echo "1. Test your API endpoints"
echo "2. Update your client applications to use HTTPS"
echo "3. Monitor certificate renewal (automatic)"
echo ""
echo "🧪 Quick Tests:"
echo "curl https://$DOMAIN/health"
echo "curl https://$DOMAIN/api/v1/institutions"
