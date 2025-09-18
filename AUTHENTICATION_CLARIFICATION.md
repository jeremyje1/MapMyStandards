# Authentication System Clarification

## Current Deployed Architecture

### What's Actually Running:
1. **FastAPI Backend** (Python) - Deployed on Railway
2. **Static HTML Frontend** (from `/web` directory) - Served by FastAPI
3. **Direct Stripe Integration** - For payments and trials

### What's NOT Deployed:
1. **Next.js Application** - Built but not serving requests
2. **NextAuth** - Configured but not active
3. **Email Magic Links** - Set up but not used

## Working Authentication Flow

### Current Trial/Signup Flow:
```
mapmystandards.ai → Free Trial Button → stripe-checkout-redirect.html → Stripe Checkout
```

This flow:
- ✅ Works without authentication
- ✅ Creates Stripe customer
- ✅ Redirects to dashboard after payment
- ✅ Is what's currently live and functional

### Login System:
- **Login Page**: https://platform.mapmystandards.ai/login-platform.html
- **Authentication**: FastAPI JWT-based (not NextAuth)
- **Backend Routes**: `/api/auth/login`, `/api/auth/register`

## Why /auth/signin Returns 404

The URL `/auth/signin` is a **Next.js route** that would exist if the Next.js app was deployed. However, what's actually deployed is:

- FastAPI serving static HTML files
- No Next.js server running
- No NextAuth routes available

## Actual Available Pages

### Working Pages:
- `/` or `/index.html` - Homepage
- `/login-platform.html` - Login page
- `/dashboard` or `/dashboard.html` - Dashboard
- `/stripe-checkout-redirect.html` - Stripe checkout flow (✅ Working)
- `/trial-signup` - Trial signup page
- `/checkout` - Checkout page

### API Endpoints:
- `/api/auth/login` - JWT login
- `/api/auth/register` - User registration
- `/api/stripe/webhook` - Stripe webhook (configured)
- `/health` - Health check

## Two Authentication Systems Exist

### 1. FastAPI JWT Authentication (ACTIVE):
- Located in: `src/a3e/api/routes/auth_impl.py`
- Uses: JWT tokens
- Login at: `/login.html`
- Status: **This is what's running**

### 2. NextAuth (CONFIGURED BUT NOT ACTIVE):
- Located in: `app/api/auth/[...nextauth]/route.ts`
- Uses: Email magic links
- Would be at: `/auth/signin`
- Status: **Not deployed**

## Why This Happened

The project has evolved through multiple iterations:
1. Started with Next.js + NextAuth
2. Added FastAPI backend for AI/ML features
3. Shifted to FastAPI serving everything
4. Next.js code remains but isn't deployed

## Current Recommendation

### Option 1: Keep Current System (Simplest)
- FastAPI + Static HTML is working
- Stripe integration is functional
- Authentication exists via JWT
- **Action**: Update documentation to reflect actual system

### Option 2: Deploy Next.js Frontend (Complex)
- Would need separate deployment for Next.js
- Configure proxy between Next.js and FastAPI
- More complex architecture
- **Action**: Deploy Next.js to Vercel, keep FastAPI on Railway

### Option 3: Hybrid Approach
- Use FastAPI for API + auth
- Gradually migrate static HTML to React components
- Keep single deployment
- **Action**: Build React components within FastAPI templates

## Testing Current Authentication

To test the actual working authentication:

1. **Visit Login Page**: https://platform.mapmystandards.ai/login-platform.html
2. **Create Account**: Use the registration flow
3. **Test Stripe Flow**: Use the working checkout redirect

## Summary

- ✅ **Stripe checkout flow works** (via stripe-checkout-redirect.html)
- ✅ **FastAPI authentication exists** (JWT-based)
- ❌ **NextAuth is not deployed** (that's why /auth/signin 404s)
- ℹ️ **Two systems were built**, only FastAPI is deployed

The system is functional but uses FastAPI's authentication, not NextAuth. The Stripe integration bypasses authentication for initial trial signups, which is why it works.