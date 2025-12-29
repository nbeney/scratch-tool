# Deploying to Render.com

This guide explains how to deploy the scratch-tool web server to Render.com using the free tier.

## Prerequisites

- ✅ Render.com account (you have this)
- ✅ GitHub repository with your code
- ✅ The Flask app is already set up in `main.py` as `flask_app`

## Overview

Render.com offers a free tier with:
- **750 hours/month** of runtime (enough for 24/7 operation)
- **512 MB RAM**
- **Automatic sleep** after 15 minutes of inactivity
- **Spin-up time** ~1 minute when waking from sleep
- **No credit card required** for free tier

## Deployment Steps

### Step 1: Prepare Your Repository

Your repository needs these files (already present):

1. **`main.py`** - Contains the Flask app (`flask_app`)
2. **`pyproject.toml`** - Contains dependencies and project metadata
3. **`render_start.sh`** - Startup script

✅ **No `requirements.txt` needed!** Render's `uv` reads directly from `pyproject.toml`.

### Step 2: Verify Start Command Script

You already have `render_start.sh` in your repository:

```bash
#!/bin/bash
# Start script for Render.com deployment

# Use gunicorn to run the Flask app
gunicorn main:flask_app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level info
```

Make it executable (locally):

```bash
chmod +x render_start.sh
```

### Step 3: Commit and Push to GitHub

```bash
git add requirements.txt render_start.sh
git commit -m "Add Render.com deployment files"
git push origin master
```

### Step 4: Create Web Service on Render

1. **Go to Render Dashboard**: https://dashboard.render.com/

2. **Click "New +"** → **"Web Service"**

3. **Connect Your Repository**:
   - If first time: Click "Configure account" to connect GitHub
   - Grant Render access to your `scratch-tool` repository
   - Select the `scratch-tool` repository

4. **Configure the Web Service**:

   | Field | Value |
   |-------|-------|
   | **Name** | `scratch-tool` (or any name you like) |
   | **Region** | Choose closest to you (e.g., `Oregon (US West)`) |
   | **Branch** | `master` (or your main branch) |
   | **Root Directory** | Leave blank (unless code is in subdirectory) |
   | **Runtime** | `Python 3` |
   | **Build Command** | `uv sync` |
   | **Start Command** | `bash render_start.sh` |
   | **Instance Type** | **Free** ⭐ |

5. **Environment Variables** (Optional):
   - Click "Advanced" to add environment variables if needed
   - For now, you don't need any

6. **Click "Create Web Service"**

### Step 5: Wait for Deployment

Render will:
1. ✅ Clone your repository
2. ✅ Install Python dependencies
3. ✅ Start your Gunicorn server
4. ✅ Assign you a URL: `https://scratch-tool-xxxx.onrender.com`

This takes about **2-5 minutes** for the first deployment.

### Step 6: Access Your App

Once deployed, you'll see:
- **Status**: "Live" (green)
- **URL**: `https://your-service-name.onrender.com`

Click the URL to access your Scratch documentation web service!

## Configuration Details

### Build Command Explained

```bash
uv sync
```

This single command:
1. Reads your `pyproject.toml` file
2. Resolves all dependencies
3. Creates/updates the virtual environment
4. Installs all packages

**Why this works on Render**:
- ✅ `uv` is pre-installed in Render's Python environment
- ✅ Reads directly from `pyproject.toml` (no `requirements.txt` needed)
- ✅ Automatically creates the virtual environment
- ✅ Faster than pip-based workflows

**Benefits of using uv sync**:
- ⚡ **10-100x faster** than pip
- 🔒 Better dependency resolution
- 💾 Smaller cache footprint
- ✅ More reliable builds
- 🎯 Uses your existing `pyproject.toml`

**Alternative commands** (if needed):
```bash
# If you want to keep requirements.txt for compatibility
pip install -r requirements.txt

# If uv is not available (older Render environments)
pip install uv && uv sync
```

### Start Command Explained

```bash
bash render_start.sh
```

This runs your start script which launches Gunicorn with:
- `--bind 0.0.0.0:${PORT}` - Binds to Render's assigned port
- `--workers 2` - 2 workers (good for 512MB RAM)
- `--timeout 120` - 2 minute timeout for Scratch API calls
- `--log-level info` - Informative logging

**Note**: Render automatically sets the `PORT` environment variable. Your app must listen on this port.

## Free Tier Behavior

### Sleep After Inactivity

Your free tier service will:
- **Sleep** after 15 minutes of no requests
- **Wake up** on the next request (takes ~1 minute)
- Show "Service is spinning up" during wake-up

This is normal and expected on the free tier!

### Prevent Sleep (Optional)

If you want to keep it awake during certain hours, you can:

1. **Use a cron job** to ping your service every 14 minutes
2. **Use a free uptime monitor**: UptimeRobot, Pingdom, etc.

Example cron job (on your local machine or another server):

```bash
# Ping every 14 minutes during work hours
*/14 9-17 * * * curl https://your-service.onrender.com/ > /dev/null 2>&1
```

**Caution**: Render's free tier has a monthly limit of 750 hours. Keeping it awake 24/7 exceeds this. Keep it awake only when needed.

## Monitoring and Logs

### View Logs

1. Go to your service in Render Dashboard
2. Click on the **"Logs"** tab
3. See real-time logs from Gunicorn

You'll see:
- Startup messages
- Incoming requests
- Any errors

### View Metrics

Click the **"Metrics"** tab to see:
- CPU usage
- Memory usage
- Request count
- Response times

## Environment Variables

If you need to configure your app, add environment variables:

1. In Render Dashboard, go to your service
2. Click **"Environment"** in the left sidebar
3. Click **"Add Environment Variable"**

Example variables you might add:

| Key | Value | Purpose |
|-----|-------|---------|
| `FLASK_ENV` | `production` | Set Flask environment |
| `LOG_LEVEL` | `info` | Control logging verbosity |
| `MAX_WORKERS` | `2` | Override worker count |

Access in your code:

```python
import os
log_level = os.environ.get('LOG_LEVEL', 'info')
```

## Custom Domain (Optional)

Render provides a free subdomain like `scratch-tool-xxxx.onrender.com`.

For a custom domain:
1. Go to **"Settings"** → **"Custom Domain"**
2. Add your domain (requires paid plan or manual DNS setup)
3. Follow Render's DNS instructions

## Updating Your Deployment

### Automatic Deployment

Render automatically redeploys when you push to your branch:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin master

# Render automatically rebuilds and deploys!
```

### Manual Deployment

1. Go to your service in Render Dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

### Clear Build Cache

If you have dependency issues:
1. Go to **"Settings"**
2. Click **"Clear build cache & deploy"**

## Troubleshooting

### Deployment Failed

**Check the Build Logs**:
1. Go to your service
2. Click **"Logs"** tab
3. Look for error messages during build

**Common Issues**:

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError` | Missing dependency in `requirements.txt` |
| `No module named 'main'` | Check `Root Directory` setting |
| `Address already in use` | Ensure using `${PORT}` variable |
| `gunicorn: command not found` | Add `gunicorn` to `requirements.txt` |

### App Won't Start

**Check Start Command**: Ensure it's exactly:
```bash
bash render_start.sh
```

Or use inline command:
```bash
gunicorn main:flask_app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### Slow Response Times

On free tier, expect:
- **First request after sleep**: ~1 minute (wake-up time)
- **Subsequent requests**: Normal speed
- **Memory issues**: Consider reducing workers to 1

### Service Keeps Sleeping

This is normal on free tier. Options:
1. **Accept it** - Free tier trade-off
2. **Ping service** - Keep awake during active hours
3. **Upgrade** - Paid plans don't sleep

### Import Errors

Ensure all files are committed:

```bash
# Check for uncommitted files
git status

# Add missing files
git add models/ scratchblocks_converter.py
git commit -m "Add missing files"
git push
```

## Optimizing for Free Tier

### Reduce Memory Usage

In `render_start.sh`, use 1 worker instead of 2:

```bash
gunicorn main:flask_app --bind 0.0.0.0:${PORT:-8000} --workers 1 --timeout 120 --log-level info
```

### Reduce Build Time

Use a minimal `requirements.txt` with exact versions:

```text
# Faster builds with pinned versions
typer==0.9.0
requests==2.31.0
pydantic==2.5.0
pygments==2.17.0
pillow==10.0.0
dominate==2.9.0
flask==3.1.0
gunicorn==21.2.0
```

### Add Health Check

Render can monitor your service. Add a health endpoint to `main.py`:

```python
@flask_app.route("/health")
def health_check():
    """Health check endpoint for Render."""
    return {"status": "healthy", "service": "scratch-tool"}, 200
```

Then configure in Render:
1. Go to **"Settings"**
2. Scroll to **"Health Check Path"**
3. Enter `/health`

## Alternative Start Commands

### Option 1: Inline Command (No script file)

Set **Start Command** to:

```bash
gunicorn main:flask_app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
```

No need for `render_start.sh` file.

### Option 2: Using the CLI Command

If you want to use your Typer CLI instead (not recommended for production):

```bash
python main.py server --host 0.0.0.0 --port $PORT
```

**Note**: This uses Flask's dev server, not recommended for production.

### Option 3: Using uv

Build command:
```bash
pip install uv && uv pip install -r requirements.txt
```

Start command:
```bash
uv run gunicorn main:flask_app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

## Comparison: Render.com vs Others

| Feature | Render Free | PythonAnywhere Free | Heroku Free |
|---------|-------------|---------------------|-------------|
| **Cost** | Free | Free | Discontinued |
| **Sleep** | After 15 min | No | After 30 min |
| **RAM** | 512 MB | 512 MB | 512 MB |
| **Hours/month** | 750 | Always on | 550 |
| **Custom domain** | ✅ Yes | ❌ No | ✅ Yes |
| **HTTPS** | ✅ Automatic | ✅ Yes | ✅ Yes |
| **Git deploy** | ✅ Automatic | ❌ Manual | ✅ Automatic |
| **Build time** | ~2 min | N/A | ~1 min |
| **Wake time** | ~1 min | N/A | ~30 sec |

## Security Best Practices

1. **Don't commit secrets**: Use environment variables
2. **Use HTTPS**: Render provides this automatically
3. **Rate limiting**: Consider adding rate limiting to prevent abuse
4. **Update dependencies**: Regularly update `requirements.txt`

## Cost Analysis

### Free Tier Limits

- **750 hours/month** = 31.25 days × 24 hours
- Your app can run 24/7 for about 31 days
- But it sleeps after 15 minutes of inactivity
- So in practice, unlimited for low-traffic apps

### When to Upgrade

Consider paid tier ($7/month) if:
- You need the service always awake
- You need more than 512 MB RAM
- You have high traffic (>100 req/min)
- You need custom domain

## Next Steps

After deploying to Render:

1. ✅ **Test your service**: Visit the URL and try documenting a project
2. 📊 **Monitor logs**: Check for any errors in the Logs tab
3. 🔔 **Set up notifications**: Configure Render to email you on deploy failures
4. 📈 **Monitor usage**: Check Metrics tab to ensure you're within limits
5. 🚀 **Share**: Your service is now publicly accessible!

## Example URLs

After deployment, your service will be accessible at:

- **Home**: `https://your-service.onrender.com/`
- **Document**: `https://your-service.onrender.com/document/1259204833`
- **Health**: `https://your-service.onrender.com/health` (if you add it)

## Getting Help

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com/
- **Gunicorn Docs**: https://docs.gunicorn.org/

## Summary Checklist

- [ ] Create `requirements.txt`
- [ ] Create `render_start.sh`
- [ ] Commit and push to GitHub
- [ ] Connect GitHub to Render
- [ ] Create Web Service on Render
- [ ] Select Free tier
- [ ] Configure build and start commands
- [ ] Deploy and wait ~2-5 minutes
- [ ] Test the deployed service
- [ ] Monitor logs for issues

**That's it!** Your Scratch documentation tool is now live on Render.com! 🎉
