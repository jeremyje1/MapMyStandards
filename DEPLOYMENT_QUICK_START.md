# 🚀 Quick Production Deployment Guide

Follow these steps to get your A³E API running on `https://api.mapmystandards.ai`

## 📋 Prerequisites

- ✅ AWS EC2 instance: `3.22.112.51` (i-0d8227bf9f9e1a1ab)
- ✅ Domain: `api.mapmystandards.ai` 
- ✅ DNS A record pointing to `3.22.112.51`

## 🎯 Quick Start (Option 1: Manual Setup)

### 1. SSH to Your Server
```bash
ssh -i your-key.pem ubuntu@3.22.112.51
```

### 2. Clone and Setup Repository
```bash
# Clone the repository
git clone https://github.com/your-org/MapMyStandards.git
cd MapMyStandards

# Make scripts executable
chmod +x scripts/*.sh

# Install system dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip git nginx certbot python3-certbot-nginx
```

### 3. Install Python Dependencies
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install fastapi uvicorn gunicorn boto3 openai pyyaml pydantic pydantic-settings
```

### 4. Configure Environment
```bash
# Copy and edit configuration
cp .env.example .env
nano .env

# Make sure these are set:
# ENVIRONMENT=production
# AWS_ACCESS_KEY_ID=***REMOVED***
# AWS_SECRET_ACCESS_KEY=***REMOVED***
# OPENAI_API_KEY=sk-proj-wyfZhcHdl0pELSA55T132q8c...
```

### 5. Start the Application
```bash
# Test locally first
./scripts/start_production.sh

# In another terminal, test it works:
curl http://127.0.0.1:8000/
```

### 6. Setup NGINX Reverse Proxy
```bash
# Setup NGINX (run in new terminal while app is running)
sudo ./scripts/setup_nginx.sh

# Test domain access
curl http://api.mapmystandards.ai/
```

### 7. Setup SSL Certificate
```bash
# Setup Let's Encrypt SSL
sudo ./scripts/setup_ssl.sh

# Test HTTPS
curl https://api.mapmystandards.ai/
```

## 🚀 Quick Start (Option 2: Automated Deployment)

For a fully automated setup:

```bash
# Clone repository
git clone https://github.com/your-org/MapMyStandards.git
cd MapMyStandards

# Run full production deployment
sudo ./scripts/deploy_production.sh
```

This will:
- Install all dependencies
- Setup system user and directories
- Create systemd service
- Configure NGINX and SSL
- Start the API automatically

## 🧪 Testing Your Deployment

Once deployed, test these endpoints:

```bash
# Basic API test
curl https://api.mapmystandards.ai/

# Health check
curl https://api.mapmystandards.ai/health

# API documentation
curl https://api.mapmystandards.ai/docs

# Integration status (with mock Canvas data)
curl https://api.mapmystandards.ai/api/v1/integrations/status

# Canvas test (mock data)
curl https://api.mapmystandards.ai/api/v1/integrations/canvas/test

# Accreditor configuration
curl https://api.mapmystandards.ai/api/v1/config/accreditors
```

## 🎯 Expected API Response

Your root endpoint should return:
```json
{
  "message": "Welcome to A3E - Autonomous Accreditation & Audit Engine",
  "version": "0.1.0",
  "environment": "production",
  "docs_url": "Documentation available upon request",
  "supported_accreditors": 4,
  "status": "operational"
}
```

## 🔧 Service Management

Once deployed as a systemd service:

```bash
# Check status
sudo systemctl status a3e

# Start/stop/restart
sudo systemctl start a3e
sudo systemctl stop a3e
sudo systemctl restart a3e

# View logs
sudo journalctl -u a3e -f

# App logs
tail -f /var/log/a3e/error.log
tail -f /var/log/a3e/access.log
```

## 🌐 Your API Endpoints

Once live, you'll have:

- **API Root**: https://api.mapmystandards.ai/
- **Health Check**: https://api.mapmystandards.ai/health
- **API Docs**: https://api.mapmystandards.ai/docs
- **Integration Status**: https://api.mapmystandards.ai/api/v1/integrations/status
- **Canvas Data**: https://api.mapmystandards.ai/api/v1/integrations/canvas/courses
- **Accreditors**: https://api.mapmystandards.ai/api/v1/config/accreditors
- **Standards Search**: https://api.mapmystandards.ai/api/v1/config/search/standards?keyword=mission

## 🎉 Success Indicators

You'll know it's working when:

1. ✅ `https://api.mapmystandards.ai/` returns the welcome message
2. ✅ `/health` returns `{"status": "healthy"}`
3. ✅ `/docs` shows the Swagger UI
4. ✅ Mock Canvas integration shows courses and outcomes
5. ✅ Accreditor data loads (SACSCOC, NECHE, WSCUC, AACSB)

## 🆘 Troubleshooting

**If the API doesn't start:**
```bash
# Check Python path and module
cd /path/to/MapMyStandards
python3 -m src.a3e.main
```

**If NGINX fails:**
```bash
# Check NGINX configuration
sudo nginx -t

# Check NGINX logs
sudo tail -f /var/log/nginx/error.log
```

**If SSL fails:**
```bash
# Check DNS propagation
nslookup api.mapmystandards.ai

# Manual SSL setup
sudo certbot --nginx -d api.mapmystandards.ai
```

You're ready to deploy! Start with the manual setup to understand each step, then use the automated deployment for future updates.
