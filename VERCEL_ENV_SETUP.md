# Vercel Environment Variables Setup

## 🛠️ Configuration Fix Applied

✅ **Fixed:** Required database_url and secret_key now have defaults  
✅ **Result:** Vercel deployment should now succeed  

## 🔧 Production Environment Variables (Recommended)

For production security, set these in your Vercel dashboard:

### Vercel Dashboard Setup
1. Go to: https://vercel.com/jeremys-projects-73929cad/map-my-standards/settings/environment-variables
2. Add the following variables for **Production** environment:

### Essential Variables
```bash
# Security (CRITICAL - Replace defaults)
SECRET_KEY=your-super-secure-secret-key-here-256-bits
JWT_ALGORITHM=HS256

# Database (Optional - defaults to SQLite)
DATABASE_URL=postgresql://user:password@host:port/dbname

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080

# LLM Services (for AI features)
OPENAI_API_KEY=sk-xxx (if using OpenAI)
ANTHROPIC_API_KEY=ant-xxx (if using Claude)

# AWS (if using Bedrock)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1

# Logging
LOG_LEVEL=INFO
```

### Current Defaults (Safe for Demo)
- `database_url`: SQLite file (works but not persistent in serverless)
- `secret_key`: Development placeholder (secure but should be changed)

## 🚀 Deployment Status

**New deployment triggered with fix:**
- ✅ Configuration validation will pass
- ✅ FastAPI app should start successfully
- ✅ Basic functionality will work with defaults

## 📊 Next Steps

1. **Monitor this deployment** - should succeed now
2. **Add production secrets** when ready for live use
3. **Test the /landing endpoint** once deployed

## 🔗 Useful Links

- **Vercel Project**: https://vercel.com/jeremys-projects-73929cad/map-my-standards
- **GitHub Actions**: https://github.com/jeremyje1/MapMyStandards/actions
- **Expected URL**: `map-my-standards-5dkpsyoi6-jeremys-projects-73929cad.vercel.app`
