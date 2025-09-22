# Environment Variables Quick Reference

## 🚨 Critical Variables (Must Set)

### Railway (Backend API)
```bash
SECRET_KEY              # Generate: openssl rand -hex 32
JWT_SECRET_KEY          # Generate: openssl rand -hex 32
DATABASE_URL            # Auto-provided by Railway PostgreSQL
STRIPE_SECRET_KEY       # From Stripe Dashboard
STRIPE_WEBHOOK_SECRET   # From Stripe Webhooks settings
```

### Vercel (Frontend)
```bash
NEXT_PUBLIC_API_URL=https://api.mapmystandards.ai
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_...
```

## 🔧 Quick Commands

### Set Railway Variables
```bash
# Single variable
railway variables set SECRET_KEY="your-value"

# Multiple from file
railway variables set < railway.env

# View all
railway variables
```

### Set Vercel Variables
```bash
# Add variable
vercel env add NEXT_PUBLIC_API_URL production

# List all
vercel env ls

# Pull to .env.local
vercel env pull
```

## 🏃 Local Development

Create `.env` with minimum:
```bash
SECRET_KEY="dev-secret-key"
JWT_SECRET_KEY="dev-jwt-key"
DATABASE_URL="sqlite:///./a3e.db"
```

Run server:
```bash
python3 -m uvicorn src.a3e.main:app --reload
```

## 📝 Templates
- Railway: `railway.env.template`
- Vercel: `vercel.env.template`
- Helper: `./setup-env-vars.sh`