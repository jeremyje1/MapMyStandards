#!/bin/bash

# Production Deployment Script for MapMyStandards A³E System
# This script sets up the complete production environment

set -e  # Exit on error

echo "🚀 Starting MapMyStandards A³E Production Deployment"
echo "=================================================="

# Configuration
DOMAIN="api.mapmystandards.ai"
WEB_DOMAIN="mapmystandards.ai"
APP_DIR="/opt/a3e"
SERVICE_USER="a3e"
PYTHON_VERSION="3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Step 1: System Updates and Dependencies
log_info "Updating system packages..."
apt update && apt upgrade -y

log_info "Installing system dependencies..."
apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    postgresql \
    postgresql-contrib \
    nginx \
    redis-server \
    git \
    curl \
    certbot \
    python3-certbot-nginx \
    supervisor \
    htop \
    ufw \
    fail2ban

# Step 2: Create Application User
log_info "Creating application user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash $SERVICE_USER
    log_success "Created user $SERVICE_USER"
else
    log_warning "User $SERVICE_USER already exists"
fi

# Step 3: Setup Application Directory
log_info "Setting up application directory..."
mkdir -p $APP_DIR
chown $SERVICE_USER:$SERVICE_USER $APP_DIR

# Step 4: Setup PostgreSQL Database
log_info "Configuring PostgreSQL..."
sudo -u postgres createdb a3e_prod || log_warning "Database a3e_prod already exists"
sudo -u postgres psql -c "CREATE USER a3e_user WITH PASSWORD 'secure_password_change_me';" || log_warning "User a3e_user already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE a3e_prod TO a3e_user;"

# Step 5: Deploy Application Code
log_info "Deploying application code..."
sudo -u $SERVICE_USER bash << EOF
cd $APP_DIR

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Copy application files
cp /Users/jeremyestrella/Desktop/MapMyStandards/simple_trial_api_v2.py ./app.py
cp /Users/jeremyestrella/Desktop/MapMyStandards/.env ./
cp -r /Users/jeremyestrella/Desktop/MapMyStandards/web ./

# Install Python dependencies
pip install --upgrade pip
pip install \
    fastapi==0.116.1 \
    uvicorn[standard]==0.35.0 \
    stripe==12.4.0 \
    python-dotenv==1.1.1 \
    psycopg2-binary==2.9.10 \
    sqlalchemy==2.0.36 \
    alembic==1.13.3 \
    redis==5.2.0 \
    celery==5.4.0 \
    sendgrid==6.11.0 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.17 \
    email-validator==2.2.0

EOF

# Step 6: Setup Environment Configuration
log_info "Configuring environment variables..."
cat > $APP_DIR/.env.prod << 'EOL'
# Production Environment Configuration
ENVIRONMENT=production
DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://a3e_user:secure_password_change_me@localhost/a3e_prod

# Stripe Configuration (Production Keys - Replace with your actual keys)
STRIPE_PUBLISHABLE_KEY="[REPLACE_WITH_YOUR_STRIPE_PUBLISHABLE_KEY]"
STRIPE_SECRET_KEY="[REPLACE_WITH_YOUR_STRIPE_SECRET_KEY]"

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Configuration
SENDGRID_API_KEY=your_sendgrid_key_here
FROM_EMAIL=noreply@mapmystandards.ai

# Security
SECRET_KEY=generate_secure_secret_key_here
JWT_SECRET_KEY=generate_jwt_secret_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
WORKERS=4

# Logging
LOG_LEVEL=INFO
EOL

chown $SERVICE_USER:$SERVICE_USER $APP_DIR/.env.prod

# Step 7: Setup Gunicorn Configuration
log_info "Configuring Gunicorn..."
cat > $APP_DIR/gunicorn.conf.py << 'EOL'
# Gunicorn Configuration for A³E API

bind = "127.0.0.1:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = "info"
accesslog = "/var/log/a3e/access.log"
errorlog = "/var/log/a3e/error.log"

# Process naming
proc_name = "a3e-api"

# Worker timeout
timeout = 30
keepalive = 2

# Preload app for better performance
preload_app = True

# User/Group
user = "a3e"
group = "a3e"
EOL

# Step 8: Setup Logging
log_info "Setting up logging..."
mkdir -p /var/log/a3e
chown $SERVICE_USER:$SERVICE_USER /var/log/a3e

# Step 9: Setup Supervisor for Process Management
log_info "Configuring Supervisor..."
cat > /etc/supervisor/conf.d/a3e.conf << 'EOL'
[program:a3e-api]
command=/opt/a3e/venv/bin/gunicorn -c /opt/a3e/gunicorn.conf.py app:app
directory=/opt/a3e
user=a3e
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/a3e/supervisor.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=ENVIRONMENT="production"
EOL

# Step 10: Setup Nginx
log_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/a3e << 'EOL'
# A³E API Server Configuration

upstream a3e_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.mapmystandards.ai;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://a3e_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://a3e_backend/health;
        access_log off;
    }
    
    # Static files
    location /static/ {
        alias /opt/a3e/web/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}

# Web dashboard server
server {
    listen 80;
    server_name dashboard.mapmystandards.ai;
    
    root /opt/a3e/web;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOL

# Enable the site
ln -sf /etc/nginx/sites-available/a3e /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Step 11: Setup SSL Certificates
log_info "Setting up SSL certificates..."
certbot --nginx -d api.mapmystandards.ai -d dashboard.mapmystandards.ai --non-interactive --agree-tos --email support@mapmystandards.ai

# Step 12: Setup Firewall
log_info "Configuring firewall..."
ufw --force enable
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS

# Step 13: Setup Fail2Ban
log_info "Configuring Fail2Ban..."
cat > /etc/fail2ban/jail.local << 'EOL'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200
EOL

# Step 14: Start Services
log_info "Starting services..."
systemctl enable postgresql
systemctl enable redis-server
systemctl enable nginx
systemctl enable supervisor
systemctl enable fail2ban

systemctl restart postgresql
systemctl restart redis-server
systemctl restart supervisor
systemctl restart nginx
systemctl restart fail2ban

# Step 15: Deploy Database Schema
log_info "Setting up database schema..."
sudo -u $SERVICE_USER bash << 'EOF'
cd /opt/a3e
source venv/bin/activate

# Create basic tables (placeholder for Alembic migrations)
python3 -c "
import psycopg2
from datetime import datetime

conn = psycopg2.connect('postgresql://a3e_user:secure_password_change_me@localhost/a3e_prod')
cur = conn.cursor()

# Create basic tables
cur.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    institution_name VARCHAR(255) NOT NULL,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(100),
    subscription_id VARCHAR(100),
    plan VARCHAR(50),
    status VARCHAR(50),
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    endpoint VARCHAR(255),
    method VARCHAR(10),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_code INTEGER
);
''')

conn.commit()
cur.close()
conn.close()
print('Database schema created successfully')
"
EOF

# Step 16: Final Health Check
log_info "Performing final health checks..."

# Check if services are running
services=("postgresql" "redis-server" "nginx" "supervisor")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        log_success "$service is running"
    else
        log_error "$service is not running"
    fi
done

# Check if API is responding
sleep 5
if curl -s http://localhost/health > /dev/null; then
    log_success "API health check passed"
else
    log_warning "API health check failed - check logs"
fi

# Step 17: Setup Monitoring (Basic)
log_info "Setting up basic monitoring..."
cat > /opt/a3e/monitor.sh << 'EOL'
#!/bin/bash
# Basic monitoring script for A³E

LOG_FILE="/var/log/a3e/monitor.log"

check_service() {
    if systemctl is-active --quiet $1; then
        echo "$(date): $1 is running" >> $LOG_FILE
    else
        echo "$(date): ERROR - $1 is not running" >> $LOG_FILE
        systemctl restart $1
    fi
}

# Check critical services
check_service "postgresql"
check_service "redis-server"
check_service "nginx"
check_service "supervisor"

# Check API health
if ! curl -s http://localhost/health > /dev/null; then
    echo "$(date): ERROR - API health check failed" >> $LOG_FILE
    supervisorctl restart a3e-api
fi
EOL

chmod +x /opt/a3e/monitor.sh

# Setup cron job for monitoring
echo "*/5 * * * * /opt/a3e/monitor.sh" | crontab -u $SERVICE_USER -

# Step 18: Deployment Summary
echo ""
echo "🎉 Deployment Complete!"
echo "====================="
log_success "A³E Production Environment is now live!"
echo ""
echo "📍 Service URLs:"
echo "   API:       https://api.mapmystandards.ai"
echo "   Dashboard: https://dashboard.mapmystandards.ai"
echo "   Health:    https://api.mapmystandards.ai/health"
echo ""
echo "📁 Important Paths:"
echo "   App Directory: $APP_DIR"
echo "   Logs:         /var/log/a3e/"
echo "   Config:       $APP_DIR/.env.prod"
echo ""
echo "🔧 Management Commands:"
echo "   Restart API:    sudo supervisorctl restart a3e-api"
echo "   View Logs:      sudo tail -f /var/log/a3e/supervisor.log"
echo "   Check Status:   sudo supervisorctl status"
echo "   Nginx Reload:   sudo systemctl reload nginx"
echo ""
echo "🔐 Security Checklist:"
echo "   ✅ Firewall configured"
echo "   ✅ SSL certificates installed"
echo "   ✅ Fail2Ban active"
echo "   ⚠️  Change default passwords in .env.prod"
echo "   ⚠️  Configure SendGrid API key"
echo ""
echo "📊 Next Steps:"
echo "   1. Test API endpoints"
echo "   2. Configure monitoring/alerts"
echo "   3. Setup backup strategy"
echo "   4. Test Stripe integration"
echo "   5. Configure custom domain"
echo ""

log_info "Deployment script completed successfully!"
