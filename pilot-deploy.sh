#!/bin/bash

# A³E Simple Pilot Deploy
# Quick deployment for pilot testing on a VPS or local server

set -e

echo "🎯 A³E Pilot Deployment"
echo "======================="

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install it first."
    echo "   apt install docker-compose-plugin"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create .env.production if it doesn't exist
if [[ ! -f ".env.production" ]]; then
    echo "🔧 Creating production environment file..."
    cp .env.production.example .env.production
    
    # Generate secure passwords
    POSTGRES_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    REDIS_PASS=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
    
    # Update the file
    sed -i "s/your_secure_postgres_password_here/$POSTGRES_PASS/g" .env.production
    sed -i "s/your_32_char_secret_key_here/$SECRET_KEY/g" .env.production  
    sed -i "s/your_secure_redis_password_here/$REDIS_PASS/g" .env.production
    
    echo "⚠️  IMPORTANT: Please edit .env.production and add:"
    echo "   - OPENAI_API_KEY=your_openai_key"
    echo "   - CANVAS_ACCESS_TOKEN=your_canvas_token"
    echo "   - Your domain name (if you have one)"
    echo ""
    read -p "Press Enter after updating .env.production..."
fi

# Build and start services
echo "🚀 Starting A³E services..."
docker-compose -f docker-compose.production.yml up -d --build

echo "⏳ Waiting for services to start (this may take 2-3 minutes)..."
sleep 30

# Check if the API is responding
echo "🔍 Checking system health..."
for i in {1..12}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ A³E is running!"
        break
    fi
    echo "   Still starting... ($i/12)"
    sleep 15
done

# Final status check
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo "🎉 A³E Pilot Deployment Complete!"
    echo "================================="
    echo ""
    echo "Your A³E system is now running at:"
    echo "🌐 Main App:    http://$(hostname -I | cut -d' ' -f1):8000"
    echo "📚 API Docs:    http://$(hostname -I | cut -d' ' -f1):8000/docs"
    echo "🔍 Health:      http://$(hostname -I | cut -d' ' -f1):8000/health"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker-compose -f docker-compose.production.yml logs -f"
    echo "  Restart:      docker-compose -f docker-compose.production.yml restart"  
    echo "  Stop:         docker-compose -f docker-compose.production.yml down"
    echo ""
    echo "Next steps:"
    echo "1. Test the API endpoints at /docs"
    echo "2. Upload some documents for analysis"
    echo "3. Test Canvas integration"
    echo "4. Share with pilot users!"
    echo ""
else
    echo "❌ Something went wrong. Check logs with:"
    echo "   docker-compose -f docker-compose.production.yml logs"
    exit 1
fi
