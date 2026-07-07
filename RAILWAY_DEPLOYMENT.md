# Railway Deployment Guide

## Prerequisites
- Railway account (you already have this)
- GitHub repository with this code pushed
- Zerodha KiteConnect API credentials

## Step 1: Push Code to GitHub

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - Ready for Railway deployment"
git remote add origin https://github.com/YOUR_USERNAME/AI-Trading-Bot.git
git push -u origin main
```

## Step 2: Connect Railway to GitHub

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **+ New Project** → **Deploy from GitHub**
3. Authorize Railway to access your GitHub
4. Select the **AI-Trading-Bot** repository
5. Click **Deploy**

Railway will automatically:
- Detect Python runtime (from requirements.txt)
- Build the Docker image
- Deploy using the Procfile

## Step 3: Set Environment Variables

In Railway dashboard:
1. Click your project
2. Go to **Variables** tab
3. Add these environment variables:

```
API_KEY=your_kite_api_key_here
API_SECRET=your_kite_api_secret_here
ACCESS_TOKEN=your_kite_access_token_here
USER_ID=your_kite_user_id_here
PORT=5000
```

## Step 4: Get Your Public URL

Railway will auto-assign a URL like: `https://your-app-xxxxxxxx.railway.app`

Visit:
- Dashboard: `https://your-app-xxxxxxxx.railway.app`
- Market Watch: `https://your-app-xxxxxxxx.railway.app/market-watch`

## Step 5: Update Frontend URLs

In `market_watch.html`, update the API endpoint from `localhost:5000` to your Railway URL:

```javascript
// Before:
const API_BASE = 'http://localhost:5000';

// After:
const API_BASE = 'https://your-app-xxxxxxxx.railway.app';
```

## Troubleshooting

### Check Logs
Railway dashboard → **Deployments** → Click latest → **View Logs**

### Common Issues

**1. "Module not found" error**
- Add to requirements.txt and push again

**2. Token expired on startup**
- Visit `/token-refresh` endpoint on your Railway URL to re-authenticate

**3. WebSocket connection failing**
- Ensure Railway allows WebSocket (it does by default)
- Check firewall/CORS settings

## Local Development

To run locally with production settings:
```bash
pip install -r requirements.txt
python app.py
```

Environment variables:
- `PORT` - defaults to 5000
- `HOST` - defaults to 0.0.0.0

## Deployment Commands (if using Railway CLI)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy from current directory
railway up

# View logs
railway logs
```

## File Structure

```
AI-Trading-Bot/
├── app.py                 # Flask backend
├── market_watch.html      # Frontend
├── instruments.csv        # Cached instruments (auto-generated)
├── kite_config.py         # Credentials (not committed)
├── requirements.txt       # Python dependencies
├── Procfile              # Railway process definition
├── Dockerfile            # Docker build config
├── railway.toml          # Railway config
└── .railwayignore        # Files to exclude
```

## Notes

- **Instruments cache** is auto-downloaded on first run from Kite API (no auth required)
- **WebSocket** connections stay open for live price streams
- **Background threads** handle token refresh and live ticker
- **CORS** is enabled for cross-origin requests

## Support

For Railway issues: [Railway Support](https://railway.app/support)
For Zerodha issues: [KiteConnect Docs](https://kite.trade/docs/connect/v3/)
