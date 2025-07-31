#!/bin/bash

# DNS Setup Script for api.mapmystandards.ai
# This script provides instructions for DNS configuration

set -e

echo "🌐 DNS Setup Instructions for api.mapmystandards.ai"
echo "=================================================="
echo ""
echo "Please follow these steps to configure DNS in Namecheap:"
echo ""

# Get current public IP if possible
if command -v curl &> /dev/null; then
    PUBLIC_IP=$(curl -s ifconfig.me || echo "Unable to detect")
    echo "📍 Detected public IP: $PUBLIC_IP"
else
    PUBLIC_IP="YOUR_SERVER_IP"
fi

echo ""
echo "1. Login to Namecheap account"
echo "2. Go to Domain List → mapmystandards.ai → Manage"
echo "3. Go to Advanced DNS tab"
echo ""
echo "4. Add these DNS records:"
echo ""
echo "   A Record:"
echo "   Type: A"
echo "   Host: api"
echo "   Value: $PUBLIC_IP"
echo "   TTL: Automatic"
echo ""
echo "   A Record (for docs subdomain):"
echo "   Type: A"
echo "   Host: docs"
echo "   Value: $PUBLIC_IP"
echo "   TTL: Automatic"
echo ""
echo "   Alternative: If using GitHub Pages or Cloudflare Pages for docs:"
echo "   Type: CNAME"
echo "   Host: docs"
echo "   Value: your-github-username.github.io"
echo "   TTL: Automatic"
echo ""

# Read EC2 IP from .env if available
if [ -f ".env" ]; then
    EC2_IP=$(grep "EC2_HOST=" .env | cut -d'=' -f2 | tr -d '"' || echo "")
    if [ ! -z "$EC2_IP" ]; then
        echo "📋 From your .env file, EC2 IP is: $EC2_IP"
        echo "   Use this IP for the DNS A records above."
        echo ""
    fi
fi

echo "5. Wait for DNS propagation (up to 24 hours, usually 1-2 hours)"
echo ""
echo "6. Verify DNS with:"
echo "   nslookup api.mapmystandards.ai"
echo "   nslookup docs.mapmystandards.ai"
echo ""
echo "🔧 Additional Configuration:"
echo ""
echo "For CDN (CloudFront):"
echo "1. Create S3 bucket: mapmystandards-artifacts"
echo "2. Create CloudFront distribution with S3 as origin"
echo "3. Add CNAME record:"
echo "   Type: CNAME"
echo "   Host: docs"
echo "   Value: [your-cloudfront-distribution].cloudfront.net"
echo ""
echo "For email (optional):"
echo "1. Add MX records for email functionality"
echo "2. Add SPF/DKIM records for email security"
echo ""

# Check if dig is available for testing
if command -v dig &> /dev/null; then
    echo "🧪 You can test DNS propagation with:"
    echo "   dig api.mapmystandards.ai"
    echo "   dig docs.mapmystandards.ai"
    echo ""
    
    # Test current DNS
    echo "Current DNS status:"
    echo "api.mapmystandards.ai:"
    dig +short api.mapmystandards.ai || echo "  Not resolved yet"
    echo "docs.mapmystandards.ai:"
    dig +short docs.mapmystandards.ai || echo "  Not resolved yet"
fi

echo ""
echo "✅ Once DNS is configured, run:"
echo "   make setup-ssl    # Configure SSL certificates"
echo "   make deploy-prod  # Deploy to production"
echo ""
echo "📚 More help: https://docs.mapmystandards.ai/deployment"
