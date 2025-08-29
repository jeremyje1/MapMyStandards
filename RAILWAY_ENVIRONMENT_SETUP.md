# Railway Environment Variables Setup Guide

## 🚂 Quick Answer: Yes, You Need to Add Environment Variables to Railway!

The environment variables in your local `.env` file are NOT automatically deployed to Railway. You must manually configure them in Railway for your production deployment to work.

## 🔴 Critical Variables Required

These MUST be set or your app won't work:

```bash
# Security (Generate NEW ones for production!)
SECRET_KEY=<generate-new-for-production>
JWT_SECRET_KEY=<generate-new-for-production>
NEXTAUTH_SECRET=<generate-new-for-production>

# Email (From your .env)
POSTMARK_API_TOKEN=6a45e155-5e3c-4f9f-9cff-45528a162248
FROM_EMAIL=noreply@mapmystandards.ai

# Database (Railway provides this automatically)
DATABASE_URL=<auto-provided-by-railway>
```

## 🚀 Fastest Setup Method

I've created an automated script for you:

```bash
# Run this command to set up all Railway environment variables
./scripts/setup_railway_env.sh
```

This script will:
1. Check Railway CLI is installed
2. Log you into Railway
3. Generate production secrets
4. Set all required variables
5. Configure your deployment

## 📋 Manual Setup (Alternative)

If you prefer to set them manually:

### Option 1: Railway CLI
```bash
# Login
railway login

# Set each variable
railway variables set SECRET_KEY=your-production-secret
railway variables set JWT_SECRET_KEY=your-jwt-key
railway variables set POSTMARK_API_TOKEN=6a45e155-5e3c-4f9f-9cff-45528a162248
# ... continue for all variables
```

### Option 2: Railway Dashboard
1. Go to https://railway.app/dashboard
2. Select your project
3. Click "Variables" tab
4. Add each variable manually or use "Raw Editor"

## 🔐 Important Security Note

**DO NOT** copy your development secrets to production!

Generate new production secrets:
```bash
# Run this to generate new production secrets
python3 scripts/generate_secrets.py
```

## 📦 Complete Variable List

### Required for Basic Operation:
- `SECRET_KEY` - Application secret
- `JWT_SECRET_KEY` - JWT signing
- `NEXTAUTH_SECRET` - NextAuth.js
- `NEXTAUTH_URL` - Your Railway app URL
- `DATABASE_URL` - PostgreSQL (auto-provided)
- `POSTMARK_API_TOKEN` - Email service
- `FROM_EMAIL` - Sender email

### Required for Payments:
- `STRIPE_SECRET_KEY` - Your live Stripe key
- `STRIPE_PUBLISHABLE_KEY` - Public Stripe key
- `STRIPE_WEBHOOK_SECRET` - After webhook setup
- `STRIPE_PRICE_*` - Your price IDs

### Configuration:
- `NODE_ENV=production`
- `PORT=8000`
- `API_HOST=0.0.0.0`
- `NEXT_PUBLIC_APP_URL` - Your Railway URL
- `API_BASE_URL` - Your Railway URL

## 🗄️ Database Setup

Railway will automatically provide DATABASE_URL when you add PostgreSQL:

```bash
railway add postgresql
```

## ✅ Quick Deployment Steps

1. **Set environment variables:**
   ```bash
   ./scripts/setup_railway_env.sh
   ```

2. **Add PostgreSQL:**
   ```bash
   railway add postgresql
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

4. **Get your URL:**
   ```bash
   railway domain
   ```

5. **Update URL variables with your actual domain:**
   ```bash
   railway variables set NEXTAUTH_URL=https://your-app.railway.app
   railway variables set NEXT_PUBLIC_APP_URL=https://your-app.railway.app
   ```

## ⚠️ Common Mistakes to Avoid

1. **Using dev secrets in production** - Always generate new ones
2. **Forgetting DATABASE_URL** - Add PostgreSQL service
3. **Wrong NEXTAUTH_URL** - Must match your Railway domain
4. **Missing Postmark token** - Email won't work without it
5. **No Stripe webhook secret** - Payments won't process

## 📊 Verification

After setting variables, verify with:
```bash
# List all variables
railway variables

# Check deployment
railway logs
```

## 🆘 Need Help?

1. Check the full checklist: `RAILWAY_ENV_CHECKLIST.md`
2. Run the automated script: `./scripts/setup_railway_env.sh`
3. View Railway logs: `railway logs`

The automated script handles everything for you. Just run it and follow the prompts!