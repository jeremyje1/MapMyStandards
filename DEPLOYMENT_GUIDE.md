# MapMyStandards A³E SaaS Platform Deployment Guide

## Overview

This guide walks you through deploying the complete MapMyStandards A³E SaaS platform with:
- Cloud-hosted API backend
- Stripe payment integration  
- WordPress website integration
- Production-ready infrastructure

## Prerequisites

1. **Stripe Account**: Get your API keys from https://dashboard.stripe.com/apikeys
2. **Cloud Platform Account**: Railway, Render, or AWS
3. **Domain Name**: For API endpoint (e.g., api.mapmystandards.ai)
4. **WordPress Site**: For customer-facing pages

## Quick Deploy Options

### Option 1: Railway (Recommended)

1. **Clone and prepare repository:**
   ```bash
   git clone https://github.com/yourusername/MapMyStandards.git
   cd MapMyStandards
   ```

2. **Set up environment:**
   ```bash
   cp production.env.example .env
   # Edit .env with your actual values
   ```

3. **Deploy to Railway:**
   - Connect your GitHub repo to Railway
   - Railway will auto-deploy using `railway.toml`
   - Set environment variables in Railway dashboard

### Option 2: Render

1. **Connect GitHub repo to Render**
2. **Create Web Service:**
   - Environment: Docker
   - Dockerfile path: `Dockerfile.production`
   - Port: 8000

### Option 3: Manual VPS

Use the provided `deploy_production.sh` script:
```bash
sudo ./deploy_production.sh
```

## Environment Configuration

Update these required environment variables:

```bash
# Stripe (Required)
STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_SECRET_KEY="sk_live_..."

# Database (Optional - uses SQLite by default)
DATABASE_URL="postgresql://user:pass@host/db"

# Domain (Required for CORS)
API_DOMAIN="api.mapmystandards.ai"
WEB_DOMAIN="mapmystandards.ai"
```

## WordPress Integration

1. **Upload the plugin:**
   ```bash
   cp -r wordpress-plugin/a3e-saas-integration /wp-content/plugins/
   ```

2. **Activate plugin** in WordPress admin

3. **Configure plugin settings:**
   - API Endpoint: `https://api.mapmystandards.ai`
   - Stripe Publishable Key: `pk_live_...`

4. **Create pages** using provided templates:
   - Checkout page
   - Dashboard page
   - Thank you page

## DNS Configuration

Point your API domain to your deployed service:

```dns
api.mapmystandards.ai    CNAME    your-service-url.railway.app
```

## SSL/HTTPS

Most cloud platforms (Railway, Render) provide automatic SSL.

For manual deployments, use Let's Encrypt:
```bash
./scripts/setup_ssl.sh
```

## Testing the Deployment

1. **Health check:**
   ```bash
   curl https://api.mapmystandards.ai/health
   ```

2. **Test trial signup:**
   - Visit: `https://yourdomain.com/checkout`
   - Complete signup form
   - Verify redirect to dashboard

3. **Verify Stripe integration:**
   - Check Stripe dashboard for customer creation
   - Test trial expiration handling

## Monitoring

### Health Checks
- `/health` - Service status
- `/` - Basic connectivity

### Logs
- Railway: View in Railway dashboard
- Render: View in Render dashboard  
- VPS: `journalctl -u a3e-api -f`

### Error Tracking
Add Sentry DSN to environment variables for error tracking.

## Security Checklist

- [ ] Environment variables configured (no hardcoded secrets)
- [ ] HTTPS enabled
- [ ] Firewall configured (if VPS)
- [ ] Database secured
- [ ] API rate limiting enabled
- [ ] CORS properly configured

## Maintenance

### Database Backups
```bash
# SQLite
cp a3e_trial.db backups/backup_$(date +%Y%m%d).db

# PostgreSQL  
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Updates
```bash
git pull origin main
# Redeploy through your platform
```

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**
   - Check if service is running
   - Verify port configuration
   - Check health endpoint

2. **CORS Errors**
   - Verify API_DOMAIN and WEB_DOMAIN settings
   - Check CORS configuration in FastAPI

3. **Stripe Errors**
   - Verify API keys are correct
   - Check Stripe webhook endpoints
   - Ensure test/live mode consistency

4. **Database Connection**
   - Verify DATABASE_URL format
   - Check database server status
   - Ensure proper credentials

### Support

- Email: support@mapmystandards.ai
- Documentation: This file
- Logs: Check your platform's logging dashboard

## Cost Estimates

### Monthly Operating Costs:
- Railway/Render: $7-25/month
- Domain: $10-15/year  
- Stripe: 2.9% + 30¢ per transaction
- Total: ~$10-30/month base + transaction fees

## Next Steps

1. Deploy the API backend
2. Configure WordPress integration
3. Test complete customer flow
4. Set up monitoring and backups
5. Launch to customers!

This completes your production-ready SaaS platform deployment.