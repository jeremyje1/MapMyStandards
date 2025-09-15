# MapMyStandards Quick Reference

## Key URLs
- **Platform**: https://platform.mapmystandards.ai
- **API**: https://api.mapmystandards.ai
- **Marketing**: https://mapmystandards.ai

## Test User Signup Flow
1. Go to: https://platform.mapmystandards.ai/trial-signup-flow.html
2. Complete signup with test email
3. Check Railway logs: `railway logs`
4. Verify user in database

## Common Commands

### Check Deployment Status
```bash
railway status
railway logs | tail -50
```

### Test API Health
```bash
curl https://api.mapmystandards.ai/health
```

### Monitor Deployment
```bash
./monitor_deployment.sh
```

### Test Fixes
```bash
python3 test_webhook_and_db.py
```

## Key Fixes Applied Today (Sept 4, 2025)

1. **Webhook Secret Updated**
   - New secret: whsec_**************** (rotated; value stored only in env)
   - Set in Railway environment

2. **Database Schema Fixed**
   - Removed conflicting models.py file
   - Using unified models from /src/a3e/models/__init__.py

3. **Pinecone Errors Fixed**
   - Added type checking for embeddings
   - Handles both list and numpy array types

## Troubleshooting

### If users still not saving:
1. Check webhook logs: `railway logs | grep webhook`
2. Verify webhook secret matches Stripe dashboard
3. Test webhook endpoint manually

### If database errors persist:
1. Check for foreign key constraints in logs
2. Verify all models use consistent types (UUID vs String)
3. Check DATABASE_URL is correct

### If Pinecone errors continue:
1. Verify PINECONE_API_KEY is set
2. Check if sentence-transformers is installed
3. Look for "tolist" errors in logs
