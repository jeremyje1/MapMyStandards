# Deployment Fix Instructions

## 1. Database Fix
Run the following SQL in your Railway PostgreSQL:
```bash
railway run psql $DATABASE_URL < fix_agent_workflows.sql
```

## 2. Deploy Updated Code
```bash
git add -A
git commit -m "Fix deployment issues: agent_workflows FK and dependencies"
git push origin main
```

## 3. Verify Deployment
After deployment, check the logs:
```bash
railway logs
```

Expected improvements:
- ✅ No more foreign key constraint errors
- ✅ Upload router should be available
- ✅ Better embeddings (numpy-based instead of dummy)
- ⚠️  Agent orchestrator warning will remain (non-critical)

## 4. Optional: Enable Agent Orchestrator
If you need multi-agent workflows, add to requirements-production.txt:
```
pyautogen==0.1.14
```

But note this will increase memory usage significantly.
