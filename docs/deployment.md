# Production Deployment Guide

## Overview

This guide covers the complete deployment process for A³E (Autonomous Accreditation & Audit Engine) to production on AWS EC2 with custom domain, SSL, and integrations.

## Prerequisites

- AWS Account with EC2 access
- Domain: mapmystandards.ai (configured in Namecheap)
- OpenAI API key
- Canvas/Banner/SharePoint credentials (optional)

## Current Infrastructure

```
Production Server: 3.22.112.51 (i-0d8227bf9f9e1a1ab)
Domain: api.mapmystandards.ai
SSL: Let's Encrypt (auto-renewal)
Reverse Proxy: NGINX
Services: Docker Compose
```

## Step 1: DNS Configuration

### Namecheap DNS Records

1. Login to Namecheap → Domain List → mapmystandards.ai → Manage
2. Go to **Advanced DNS** tab
3. Add these records:

```
Type: A Record
Host: api
Value: 3.22.112.51
TTL: Automatic

Type: A Record  
Host: docs
Value: 3.22.112.51
TTL: Automatic
```

### Verify DNS

```bash
# Test DNS propagation
nslookup api.mapmystandards.ai
dig api.mapmystandards.ai

# Should return: 3.22.112.51
```

## Step 2: Server Setup

### Connect to EC2

```bash
# SSH to server
ssh -i your-key.pem ubuntu@3.22.112.51

# Or from local machine
make ssh-server
```

### Install Dependencies

```bash
# Run setup script
./scripts/setup_server.sh

# Or manually:
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx git
sudo systemctl enable docker
sudo usermod -aG docker ubuntu
```

## Step 3: Deploy Application

### Clone and Configure

```bash
# Clone repository
git clone https://github.com/your-org/MapMyStandards.git
cd MapMyStandards

# Copy environment file
cp .env.example .env

# Edit configuration
nano .env
```

### Environment Configuration

Ensure these variables are set in `.env`:

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql://a3e:production_password@localhost:5432/a3e

# AWS & LLM
AWS_ACCESS_KEY_ID=***REMOVED***
AWS_SECRET_ACCESS_KEY=***REMOVED***
OPENAI_API_KEY=sk-proj-wyfZhcHdl0pELSA55T132q8c...

# Domain
API_DOMAIN=api.mapmystandards.ai
EC2_HOST=3.22.112.51
EC2_INSTANCE_ID=i-0d8227bf9f9e1a1ab

# Integrations (optional)
CANVAS_CLIENT_ID=your_canvas_client_id
CANVAS_CLIENT_SECRET=your_canvas_secret
MS_CLIENT_ID=your_azure_app_id
MS_CLIENT_SECRET=your_azure_secret
MS_TENANT_ID=your_tenant_id
```

## Step 4: SSL Configuration

### Setup NGINX + SSL

```bash
# Configure NGINX reverse proxy
sudo ./scripts/setup_nginx.sh

# Setup SSL certificates
sudo ./scripts/setup_ssl.sh

# Verify SSL
curl -I https://api.mapmystandards.ai
```

### SSL Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Crontab for auto-renewal (already configured)
sudo crontab -l
# Should show: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Step 5: Application Deployment

### Production Build

```bash
# Build and start services
make build-prod
make deploy-prod

# Or manually:
docker-compose -f docker-compose.prod.yml up -d --build
```

### Database Initialization

```bash
# Create database and run migrations
make setup-db
make migrate
make seed

# Or manually:
docker-compose exec app alembic upgrade head
docker-compose exec app python -m src.a3e.scripts.seed_data
```

## Step 6: Integration Setup

### Canvas LMS Integration

1. Login to Canvas as admin
2. Go to **Developer Keys**
3. Create new API key:
   - Redirect URI: `https://api.mapmystandards.ai/callback`
   - Scopes: `courses:read`, `users:read`, `outcomes:read`
4. Copy Client ID and Secret to `.env`

### Banner SIS Integration

**Option 1: Ethos API**
```bash
# Get Bearer Token and base URL from IT team
BANNER_ETHOS_TOKEN=your_bearer_token
BANNER_ETHOS_BASE_URL=https://integrate.elluciancloud.com
```

**Option 2: Direct Database**
```bash
# Get database credentials from IT team
BANNER_DB_HOST=banner.yourschool.edu
BANNER_DB_PORT=1521
BANNER_DB_USER=a3e_readonly
BANNER_DB_PASSWORD=secure_password
BANNER_DB_SCHEMA=GENERAL
```

### SharePoint Integration

1. Go to [Azure Portal](https://portal.azure.com)
2. App Registrations → New registration
3. Set redirect URI: `https://api.mapmystandards.ai/oauth-callback`
4. Grant permissions: `Sites.Read.All`, `Files.Read.All`
5. Copy client_id, tenant_id, client_secret to `.env`

## Step 7: Monitoring & Testing

### Health Checks

```bash
# API health
curl https://api.mapmystandards.ai/health

# Integration status
curl https://api.mapmystandards.ai/api/v1/integrations/status

# Service logs
docker-compose logs -f app
```

### Performance Monitoring

```bash
# System resources
docker stats

# Application metrics
curl https://api.mapmystandards.ai/metrics

# Database performance
docker-compose exec postgres psql -U a3e -c "SELECT * FROM pg_stat_activity;"
```

## Step 8: CDN & Document Storage

### S3 + CloudFront Setup

```bash
# Create S3 bucket
aws s3 mb s3://mapmystandards-artifacts

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Update DNS with CloudFront domain
# Type: CNAME, Host: docs, Value: d123456.cloudfront.net
```

## API Endpoints

### Core API
- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation

### Institutions
- `GET /api/v1/institutions` - List institutions
- `POST /api/v1/institutions` - Create institution
- `GET /api/v1/institutions/{id}` - Get institution details

### Standards & Evidence
- `GET /api/v1/standards` - List standards
- `POST /api/v1/evidence` - Upload evidence
- `POST /api/v1/workflows/map-evidence` - Map evidence to standards

### Configuration
- `GET /api/v1/config/accreditors` - List accreditors
- `GET /api/v1/config/institution-types` - Institution types
- `GET /api/v1/config/evidence-tags` - Evidence classification tags

### Integrations
- `GET /api/v1/integrations/status` - Integration status
- `POST /api/v1/integrations/sync` - Sync data from LMS/SIS
- `GET /api/v1/integrations/canvas/courses` - Canvas courses
- `GET /api/v1/integrations/sharepoint/sites` - SharePoint sites

## Troubleshooting

### Common Issues

**SSL Certificate Issues**
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew

# Restart nginx
sudo systemctl restart nginx
```

**Database Connection Issues**
```bash
# Check database status
docker-compose exec postgres psql -U a3e -c "SELECT version();"

# Reset database
make reset-db
make seed
```

**Integration Authentication Failures**
```bash
# Test Canvas connection
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://yourschool.instructure.com/api/v1/users/self

# Test SharePoint connection
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://graph.microsoft.com/v1.0/sites
```

### Logs & Debugging

```bash
# Application logs
docker-compose logs -f app

# NGINX logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u nginx -f
sudo journalctl -u docker -f
```

## Maintenance

### Regular Tasks

```bash
# Update application
git pull origin main
make deploy-prod

# Backup database
docker-compose exec postgres pg_dump -U a3e a3e > backup_$(date +%Y%m%d).sql

# Monitor disk space
df -h
docker system prune -f

# Update SSL certificates (automated)
sudo certbot renew --quiet
```

### Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Review security logs
sudo grep "Failed password" /var/log/auth.log
```

## Support

- **Documentation**: https://docs.mapmystandards.ai
- **API Reference**: https://api.mapmystandards.ai/docs
- **Issues**: GitHub Issues
- **Email**: support@mapmystandards.ai

## Architecture Summary

```mermaid
graph TB
    A[Namecheap DNS] --> B[api.mapmystandards.ai]
    B --> C[AWS EC2 3.22.112.51]
    C --> D[NGINX Reverse Proxy]
    D --> E[Docker Compose]
    E --> F[FastAPI Application]
    E --> G[PostgreSQL Database]
    E --> H[Milvus Vector DB]
    E --> I[Redis Cache]
    F --> J[AWS Bedrock]
    F --> K[OpenAI API]
    F --> L[Canvas LMS]
    F --> M[Banner SIS]
    F --> N[SharePoint]
```

## Accreditor Support

The system supports all major US accrediting bodies:

- **Regional**: SACSCOC, NECHE, MSCHE, HLC, WSCUC, NWCCU
- **National**: DEAC, TRACS, ACICS
- **Programmatic**: AACSB, ABET, LCME, ABA, NASAD, NASM

Configuration is managed through `config/standards_config.yaml` with specific mapping rules and evidence requirements for each accreditor.
