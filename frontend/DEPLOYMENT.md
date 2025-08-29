# Deploying React Frontend to Railway

## Quick Start

1. **Install Railway CLI** (if not already installed):
```bash
npm install -g @railway/cli
```

2. **Login to Railway**:
```bash
railway login
```

3. **Create a new service for the frontend**:
```bash
cd frontend
railway link  # Link to your existing project
railway service create frontend  # Create a new service named 'frontend'
```

4. **Set environment variables**:
```bash
railway variables set REACT_APP_API_URL=https://api.mapmystandards.ai
railway variables set REACT_APP_STRIPE_PUBLISHABLE_KEY=pk_live_51Rxag5RMpSG47vNmE0GkLZ6xVBlXC2D8TS5FUSDI4VoKc5mJOzZu8JOKzmMMYMLtAONF7wJUfz6Wi4jKpbS2rBEi00tkzmeJgx
railway variables set NODE_ENV=production
```

5. **Deploy**:
```bash
railway up
```

## Domain Configuration

After deployment, set up your custom domain:

1. Go to Railway dashboard
2. Select the frontend service
3. Go to Settings → Domains
4. Add custom domain: `app.mapmystandards.ai`
5. Update DNS records as instructed

## Verify Deployment

1. Check deployment status:
```bash
railway status
```

2. View logs:
```bash
railway logs
```

3. Test the health endpoint:
```bash
curl https://app.mapmystandards.ai/health
```

## Update Backend CORS

Ensure the FastAPI backend allows requests from the React frontend domain. The CORS configuration has already been updated to include:
- `https://app.mapmystandards.ai`
- `http://localhost:3000`
- `http://localhost:3001`