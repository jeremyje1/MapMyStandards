# Security Guidelines for MapMyStandards

## 🔒 Secret Management Best Practices

### Never Commit These Files
- ❌ `.env` (production credentials)
- ❌ `.env.local` (local development secrets)
- ❌ `.env.production` (production secrets)
- ❌ Any file containing actual API keys, passwords, or tokens
- ✅ `.env.example` (template with placeholders only)
- ✅ `.env.complete.example` (full template with documentation)

### Where to Store Secrets

#### ✅ Production Secrets
- **Railway**: Use Railway CLI or Dashboard
  ```bash
  railway variables --set SECRET_NAME=secret_value
  ```
- **Vercel**: Use Vercel CLI or Dashboard
  ```bash
  vercel env add SECRET_NAME production
  ```
- **AWS**: Use AWS Secrets Manager or Parameter Store
- **Never** in git repositories
- **Never** in local `.env` files that could be committed

#### ✅ Development Secrets
- Use `.env.local` (already in .gitignore)
- Copy from `.env.example` and fill in your values
- Keep personal credentials separate from shared templates

### Secret Safeguards in Place

#### 1. Git-Level Protection
- **`.gitignore`**: Blocks all `.env*` files except examples
- **`.gitleaks.toml`**: Scans for 15+ types of secrets (AWS, OpenAI, Stripe, etc.)
- **GitHub Secret Scanning**: Automatically blocks pushes with detected secrets

#### 2. Pre-Commit Hooks (`.pre-commit-config.yaml`)
Install once with:
```bash
pip install pre-commit
pre-commit install
```

Automatically checks before every commit:
- ✅ Blocks `.env` files (except `.env.example`)
- ✅ Detects private keys
- ✅ Scans for AWS credentials
- ✅ Runs GitLeaks secret detection
- ✅ Checks for hardcoded API keys in Python
- ✅ Validates secrets use `os.environ` or `getenv()`
- ✅ Prevents direct commits to `main` branch

#### 3. Environment Variable Patterns
Always use environment variables for secrets:

✅ **Correct:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
db_password = os.environ['POSTGRES_PASSWORD']
```

❌ **Incorrect:**
```python
# NEVER hardcode secrets
api_key = "<hardcoded API key>"
db_password = "<hardcoded password>"
```

### Quick Start - Setting Up Protection

1. **Install pre-commit hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. **Install GitLeaks (optional but recommended):**
   ```bash
   # macOS
   brew install gitleaks

   # Linux
   wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.1/gitleaks_8.18.1_linux_x64.tar.gz
   tar -xzf gitleaks_8.18.1_linux_x64.tar.gz
   sudo mv gitleaks /usr/local/bin/
   ```

3. **Test the protection:**
   ```bash
   # This should be blocked by pre-commit
   echo "OPENAI_API_KEY=YOUR_ACTUAL_KEY" > .env.test
   git add .env.test
   git commit -m "test"  # Will fail with error
   ```

4. **Use environment templates:**
   ```bash
   # Start new development
   cp .env.example .env.local
   # Edit .env.local with your actual secrets (never commit this file)
   ```

### Credential Rotation Checklist

When rotating credentials (do this every 90 days or after exposure):

- [ ] Generate new secure credentials
- [ ] Update Railway variables via CLI
- [ ] Update Vercel environment variables
- [ ] Update AWS Secrets Manager (if used)
- [ ] Delete old credentials from providers
- [ ] Test deployment with new credentials
- [ ] Delete any local `.env` files with old credentials
- [ ] Update team password manager (if used)
- [ ] Document rotation in `CREDENTIAL_ROTATION_SUMMARY.md`

### Emergency Response - If Secrets Are Exposed

1. **Immediate Action:**
   ```bash
   # Rotate the exposed credential IMMEDIATELY
   # For OpenAI:
   # 1. Go to https://platform.openai.com/api-keys
   # 2. Delete exposed key
   # 3. Create new key
   # 4. Update in Railway/Vercel

   # For AWS:
   # 1. Go to AWS IAM Console
   # 2. Deactivate exposed key
   # 3. Create new key
   # 4. Update in Railway/Vercel
   # 5. Delete old key
   ```

2. **Clean Git History (if committed):**
   ```bash
   # Remove sensitive file from all history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env.production" \
     --prune-empty --tag-name-filter cat -- --all

   # Force push (DANGER - coordinate with team first)
   git push origin --force --all
   ```

3. **Run Security Audit:**
   ```bash
   # Check for other exposed secrets
   gitleaks detect --source . --verbose

   # Review all environment variables
   railway variables
   vercel env ls
   ```

4. **Document Incident:**
   - Create `SECURITY_INCIDENT_[DATE].md`
   - Document what was exposed
   - Document rotation steps taken
   - Document lessons learned

### Security Monitoring

#### Regular Audits (Monthly)
```bash
# Check for secrets in codebase
gitleaks detect --source . --verbose --report-path security-audit.json

# Review Railway variables
railway variables | grep -E "(KEY|PASSWORD|SECRET|TOKEN)"

# Check Vercel environment variables
vercel env ls
```

#### Dependency Security (Weekly)
```bash
# Python dependencies
pip install safety
safety check --json

# Node.js dependencies
npm audit

# Check for outdated packages
pip list --outdated
npm outdated
```

### Additional Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitLeaks Documentation](https://github.com/gitleaks/gitleaks)
- [Railway Environment Variables](https://docs.railway.app/develop/variables)
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

### Team Responsibilities

**All Developers:**
- Never commit secrets to git
- Use `.env.local` for local development
- Run `pre-commit run --all-files` before pushing
- Report any suspected secret exposure immediately

**DevOps/Security Lead:**
- Rotate all production secrets every 90 days
- Monitor GitHub secret scanning alerts
- Audit Railway/Vercel environment variables monthly
- Review access logs for suspicious activity

**Project Lead:**
- Approve all credential rotations
- Maintain documentation of security incidents
- Ensure team training on security best practices
- Budget for security tools (secret managers, monitoring)

---

**Last Updated:** October 10, 2025
**Last Credential Rotation:** October 10, 2025
**Next Rotation Due:** January 8, 2026
