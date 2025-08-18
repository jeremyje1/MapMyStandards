# GitHub Authentication Setup

## Issue
Git push failed because GitHub requires token authentication, not password.

## Solution Options

### Option 1: Personal Access Token (Recommended)
1. Go to GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with these scopes:
   - `repo` (full control of private repositories)
   - `workflow` (if you want to trigger actions)
3. Copy the token (starts with `ghp_`)
4. Use token as password when prompted:
   ```bash
   git push -u origin main
   # Username: jeremyje1
   # Password: [paste your token here]
   ```

### Option 2: Configure Git with Token
Store token in git config (one-time setup):
```bash
git remote set-url origin https://jeremyje1:YOUR_TOKEN@github.com/jeremyje1/MapMyStandards.git
git push -u origin main
```

### Option 3: SSH Keys (Most Secure)
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your-email@example.com"`
2. Add to GitHub: Settings → SSH and GPG keys → New SSH key
3. Change remote to SSH: `git remote set-url origin git@github.com:jeremyje1/MapMyStandards.git`
4. Push: `git push -u origin main`

### Option 4: GitHub CLI (Easiest)
```bash
# Install GitHub CLI
brew install gh
# Authenticate
gh auth login
# Push will work automatically after auth
git push -u origin main
```

## After Authentication Works
The GitHub Actions workflow will automatically deploy to Vercel when you push.

## Next Steps
1. Set up authentication using one of the options above
2. Push the code: `git push -u origin main`
3. Monitor deployment in GitHub Actions tab
4. Check Vercel deployment status

Your Vercel project: `prj_535SlKWMzZrP8HHG0Mb44JAIEK97`
