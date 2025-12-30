# Render.com Deployment - Quick Reference

## 📋 Render Service Configuration

When setting up your Web Service on Render.com, use these exact values:

| Setting | Value |
|---------|-------|
| **Name** | `scratch-tool` (or your choice) |
| **Region** | Choose closest to you |
| **Branch** | `master` |
| **Runtime** | `Python 3` |
| **Build Command** | `uv sync` |
| **Start Command** | `bash render_start.sh` |
| **Plan** | **Free** ⭐ |

## 📁 Required Files (Already Created)

✅ `pyproject.toml` - Python dependencies and metadata
✅ `render_start.sh` - Startup script
✅ `main.py` - Flask app (flask_app)

**Note**: You don't need `requirements.txt` - `uv` reads from `pyproject.toml` directly!

## 🚀 Deployment Steps

### 1. Commit and Push

```bash
git add render_start.sh
git commit -m "Add Render deployment files"
git push origin master
```

**Note**: `pyproject.toml` and `main.py` are already in your repo!

### 2. Create Web Service on Render

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select `scratch-tool` repository
5. Fill in the configuration (see table above)
6. Click **"Create Web Service"**

### 3. Wait for Deployment

⏱️ First deploy takes ~1-2 minutes

You'll get a URL like: `https://scratch-tool-xxxx.onrender.com`

## 🔄 Auto-Deploy (Enabled by Default!)

✅ **Auto-deploy is ON by default** when you connect a GitHub repository!

### How It Works

```
Code Change → git push → GitHub → Render → Auto Deploy! 🚀
```

### Quick Update Workflow

```bash
# 1. Make changes
vim main.py

# 2. Commit and push
git add main.py
git commit -m "Update feature"
git push origin master

# 3. Render automatically deploys! (1-2 min)
# Check progress: Dashboard → Events tab
```

### Verify Auto-Deploy

1. Go to Render Dashboard → Your Service
2. Click **"Settings"**
3. Check **"Auto-Deploy"** is enabled

**See**: [RENDER_AUTO_DEPLOY.md](RENDER_AUTO_DEPLOY.md) for full guide on auto-deployment.

## 🎯 Alternative Start Commands

If `bash render_start.sh` doesn't work, try these:

### Option 1: Direct Gunicorn (Recommended)

```bash
gunicorn main:flask_app --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -
```

### Option 2: Single Worker (Less Memory)

```bash
gunicorn main:flask_app --bind 0.0.0.0:$PORT --workers 1 --timeout 120
```

### Option 3: With Shell Script

```bash
sh render_start.sh
```

### Build Command Alternatives

**Using uv sync (recommended):**
```bash
uv sync
```
This reads from `pyproject.toml` directly - fastest and simplest!

**Using pip (if uv unavailable):**
```bash
pip install -r requirements.txt
```
Requires `requirements.txt` file in your repo.

## ⚡ Free Tier Behavior

- 🟢 **Active**: Responds normally
- 😴 **Sleeps**: After 15 minutes of inactivity
- ⏰ **Wake time**: ~1 minute on next request
- 📊 **Limit**: 750 hours/month (enough for 24/7)

## 📊 Monitoring

### View Logs

Dashboard → Your Service → **Logs** tab

### View Metrics

Dashboard → Your Service → **Metrics** tab

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Build fails** | Check `requirements.txt` has all dependencies |
| **App won't start** | Verify Start Command uses `$PORT` variable |
| **Module not found** | Add missing imports to `requirements.txt` |
| **Slow first load** | Normal - service waking from sleep |
| **404 on routes** | Check Flask routes in `main.py` |

## 🔄 Update Deployment

Render auto-deploys on push:

```bash
# Make changes
git add .
git commit -m "Update"
git push

# Render automatically rebuilds!
```

Or click **"Manual Deploy"** in Render Dashboard.

## 🎨 Example URLs

After deployment:

- **Home**: `https://your-service.onrender.com/`
- **Document Project**: `https://your-service.onrender.com/document/1259204833`

## 💡 Tips

1. **First request is slow** - Service wakes from sleep (~1 min)
2. **Keep awake** - Use UptimeRobot to ping every 14 minutes
3. **Monitor usage** - Check Metrics to stay within limits
4. **Custom domain** - Available on paid plans ($7/month)

## 📝 Quick Commands

```bash
# Test locally with simulated PORT variable
PORT=8000 bash render_start.sh

# View local requirements
cat requirements.txt

# Check Git status
git status

# Force rebuild on Render
# Dashboard → Settings → "Clear build cache & deploy"
```

## 🆘 Getting Help

- **Render Docs**: https://render.com/docs
- **Community**: https://community.render.com/
- **Full Guide**: See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

---

**Ready?** Push your code and create your Web Service on Render! 🚀
