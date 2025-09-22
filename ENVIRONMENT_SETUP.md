# Environment Variables Configuration Guide

## Railway Configuration

### Required Environment Variables

These environment variables must be set in Railway for the backend API:

#### Core Application
```bash
# Required secrets (generate secure random values)
SECRET_KEY="your-secret-key-here"  # Generate with: openssl rand -hex 32
JWT_SECRET_KEY="your-jwt-secret-here"  # Generate with: openssl rand -hex 32

# Application settings
RAILWAY_ENVIRONMENT="production"
DEBUG="false"
API_PORT="8000"
```

#### Database
```bash
# Railway provides this automatically when you provision a PostgreSQL database
DATABASE_URL="postgresql://user:password@host:port/database"
DATABASE_POOL_SIZE="20"
DATABASE_MAX_OVERFLOW="30"
```

#### API Keys
```bash
# AI/LLM Services
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."

# AWS (for Bedrock if used)
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"
AWS_REGION="us-east-1"
BEDROCK_REGION="us-east-1"
```

#### Email Configuration (Postmark)
```bash
POSTMARK_SERVER_TOKEN="your-postmark-token"
POSTMARK_API_KEY="your-postmark-api-key"
EMAIL_FROM="support@mapmystandards.ai"
EMAIL_FROM_NAME="MapMyStandards A³E"
ADMIN_NOTIFICATION_EMAIL="info@northpathstrategies.org"
```

#### Payment (Stripe)
```bash
STRIPE_SECRET_KEY="sk_live_..."
STRIPE_PUBLISHABLE_KEY="pk_live_..."
STRIPE_WEBHOOK_SECRET="whsec_..."

# Price IDs from Stripe
STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY="price_..."
STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL="price_..."
STRIPE_PRICE_ID_INSTITUTION_MONTHLY="price_..."
STRIPE_PRICE_ID_INSTITUTION_ANNUAL="price_..."
```

#### Public URLs
```bash
PUBLIC_APP_URL="https://platform.mapmystandards.ai"
PUBLIC_API_URL="https://api.mapmystandards.ai"
```

#### CORS Configuration
```bash
CORS_ORIGINS="https://platform.mapmystandards.ai,https://www.mapmystandards.ai"
```

### How to Set Railway Environment Variables

1. **Via Railway CLI:**
```bash
# Set a single variable
railway variables set SECRET_KEY="your-secret-key-here"

# Set multiple variables from a file
railway variables set < railway.env
```

2. **Via Railway Dashboard:**
- Go to your project in Railway
- Select the service
- Click on "Variables" tab
- Add each variable manually or bulk import

## Vercel Configuration

### Required Environment Variables for Frontend

These need to be set in Vercel for the web frontend:

```bash
# API Configuration
NEXT_PUBLIC_API_URL="https://api.mapmystandards.ai"
VITE_API_URL="https://api.mapmystandards.ai"

# Stripe Public Key
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY="pk_live_..."
VITE_STRIPE_PUBLISHABLE_KEY="pk_live_..."

# Google OAuth (if using)
NEXT_PUBLIC_GOOGLE_CLIENT_ID="your-google-client-id"

# Feature flags
NEXT_PUBLIC_ENABLE_ANALYTICS="true"
```

### How to Set Vercel Environment Variables

1. **Via Vercel CLI:**
```bash
# Add environment variables
vercel env add NEXT_PUBLIC_API_URL production

# Pull existing variables
vercel env pull
```

2. **Via Vercel Dashboard:**
- Go to your project settings
- Navigate to "Environment Variables"
- Add variables for Production/Preview/Development

## Local Development Setup

Create a `.env` file in the root directory:

```bash
# Copy from .env.example if exists
cp .env.example .env

# Edit with your local values
```

### Minimum local .env content:
```bash
# Required for local development
SECRET_KEY="local-dev-secret-key"
JWT_SECRET_KEY="local-dev-jwt-key"

# Database (local PostgreSQL or SQLite)
DATABASE_URL="sqlite:///./a3e.db"

# API Keys (use test keys)
STRIPE_SECRET_KEY="sk_test_..."
POSTMARK_API_KEY="test-key"

# Development URLs
PUBLIC_APP_URL="http://localhost:3000"
PUBLIC_API_URL="http://localhost:8000"
CORS_ORIGINS="http://localhost:3000,http://localhost:8080"

# Optional: AI keys for testing
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
```

## Security Best Practices

1. **Never commit secrets to git**
   - Use `.gitignore` to exclude `.env` files
   - Store production secrets only in Railway/Vercel

2. **Generate secure keys:**
```bash
# Generate SECRET_KEY
openssl rand -hex 32

# Generate JWT_SECRET_KEY
openssl rand -hex 32
```

3. **Use different keys for each environment**
   - Development, staging, and production should have unique keys

4. **Rotate keys regularly**
   - Update SECRET_KEY and JWT_SECRET_KEY periodically
   - Update API keys when needed

## Validation

After setting environment variables:

1. **Check Railway deployment:**
```bash
railway logs
railway run echo $SECRET_KEY  # Should show [REDACTED]
```

2. **Check Vercel deployment:**
```bash
vercel env ls
```

3. **Test the deployment:**
```bash
# Check API health
curl https://api.mapmystandards.ai/health

# Check frontend
curl https://platform.mapmystandards.ai
```