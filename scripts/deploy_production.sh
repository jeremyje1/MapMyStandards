#!/bin/bash

# Production Deployment Script for A³E API
# Deploys the application with Gunicorn + NGINX + SSL

set -e

echo "🚀 A³E Production Deployment"
echo "============================"

# Configuration
APP_NAME="a3e"
APP_USER="ubuntu"
APP_DIR="/opt/a3e"
REPO_URL="https://github.com/your-org/MapMyStandards.git"
DOMAIN="api.mapmystandards.ai"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

echo "📦 Installing system dependencies..."

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3.12 python3.12-venv python3-pip git nginx certbot python3-certbot-nginx \
    postgresql-client redis-tools curl wget htop supervisor

# Install Poetry
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="/root/.local/bin:$PATH"
fi

echo "👤 Setting up application user and directories..."

# Create application user if doesn't exist
if ! id "$APP_USER" &>/dev/null; then
    useradd --system --shell /bin/bash --home-dir $APP_DIR --create-home $APP_USER
fi

# Create directories
mkdir -p $APP_DIR
mkdir -p /var/log/a3e
mkdir -p /var/run/a3e

# Set permissions
chown -R $APP_USER:$APP_USER $APP_DIR
chown -R $APP_USER:$APP_USER /var/log/a3e
chown -R $APP_USER:$APP_USER /var/run/a3e

echo "📂 Deploying application code..."

# Deploy application
if [ -d "$APP_DIR/.git" ]; then
    echo "Updating existing repository..."
    cd $APP_DIR
    sudo -u $APP_USER git pull origin main
else
    echo "Cloning repository..."
    sudo -u $APP_USER git clone $REPO_URL $APP_DIR
    cd $APP_DIR
fi

echo "📦 Installing Python dependencies..."

# Install dependencies
sudo -u $APP_USER /root/.local/bin/poetry install --only=main --no-dev

echo "⚙️  Setting up configuration..."

# Copy production environment file
if [ ! -f "$APP_DIR/.env" ]; then
    echo "Creating production .env file..."
    sudo -u $APP_USER cp $APP_DIR/.env.example $APP_DIR/.env
    echo "⚠️  Please update $APP_DIR/.env with production values"
fi

# Set up logging
cat > /etc/logrotate.d/a3e << EOF
/var/log/a3e/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 $APP_USER $APP_USER
    postrotate
        systemctl reload a3e
    endscript
}
EOF

echo "🔧 Creating systemd service..."

# Create systemd service
cat > /etc/systemd/system/a3e.service << EOF
[Unit]
Description=A³E (Autonomous Accreditation & Audit Engine) API
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH="$APP_DIR/.venv/bin"
ExecStart=$APP_DIR/.venv/bin/gunicorn -c $APP_DIR/config/gunicorn.conf.py src.a3e.main:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$APP_DIR /var/log/a3e /var/run/a3e /tmp

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable a3e

echo "🌐 Setting up NGINX..."

# Run NGINX setup script
cd $APP_DIR
./scripts/setup_nginx.sh

echo "🔒 Setting up SSL..."

# Run SSL setup script
./scripts/setup_ssl.sh

echo "🗄️  Setting up database..."

# Run database initialization (if needed)
if [ -f "$APP_DIR/scripts/init_db.sql" ]; then
    echo "Initializing database..."
    # This would connect to your PostgreSQL instance
    # psql -h localhost -U a3e -d a3e -f $APP_DIR/scripts/init_db.sql
fi

echo "🚀 Starting services..."

# Start A³E service
systemctl start a3e
systemctl status a3e --no-pager

echo "🧪 Testing deployment..."

# Wait a moment for service to start
sleep 5

# Test local connection
if curl -f http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ Local API responding"
else
    echo "❌ Local API not responding"
    systemctl status a3e --no-pager
    exit 1
fi

# Test domain connection
if curl -f http://$DOMAIN/health > /dev/null 2>&1; then
    echo "✅ Domain API responding"
else
    echo "⚠️  Domain not responding (DNS may need to propagate)"
fi

# Test HTTPS if SSL is set up
if curl -f https://$DOMAIN/health > /dev/null 2>&1; then
    echo "✅ HTTPS API responding"
else
    echo "⚠️  HTTPS not responding (SSL may need setup)"
fi

echo ""
echo "🎉 A³E Production Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Service Management:"
echo "  Start:   sudo systemctl start a3e"
echo "  Stop:    sudo systemctl stop a3e"
echo "  Restart: sudo systemctl restart a3e"
echo "  Status:  sudo systemctl status a3e"
echo "  Logs:    sudo journalctl -u a3e -f"
echo ""
echo "🌐 API Endpoints:"
echo "  HTTP:  http://$DOMAIN/"
echo "  HTTPS: https://$DOMAIN/"
echo "  Docs:  https://$DOMAIN/docs"
echo "  Health: https://$DOMAIN/health"
echo ""
echo "📂 Important Paths:"
echo "  App Dir: $APP_DIR"
echo "  Logs: /var/log/a3e/"
echo "  Config: $APP_DIR/.env"
echo ""
echo "🔧 Next Steps:"
echo "1. Update $APP_DIR/.env with production configuration"
echo "2. Test all API endpoints"
echo "3. Set up monitoring and backups"
echo "4. Configure CI/CD pipeline"
