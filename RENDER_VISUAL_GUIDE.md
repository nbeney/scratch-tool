# Render.com Deployment - Step by Step Visual Guide

## 📊 Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│  LOCAL MACHINE                                              │
│                                                             │
│  1. Create deployment files:                               │
│     ✅ pyproject.toml (Python dependencies)                │
│     ✅ render_start.sh (Startup script)                    │
│     ✅ main.py (Flask app: flask_app)                      │
│                                                             │
│  2. Commit and push:                                       │
│     $ git add render_start.sh                              │
│     $ git commit -m "Add Render deployment"                │
│     $ git push origin master                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ git push
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  GITHUB                                                     │
│                                                             │
│  📂 Repository: username/scratch-tool                      │
│     ├── main.py                                            │
│     ├── requirements.txt                                   │
│     ├── render_start.sh                                    │
│     ├── models/                                            │
│     └── ...                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ webhook
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  RENDER.COM                                                 │
│                                                             │
│  3. Create Web Service:                                    │
│     • Connect GitHub repo                                  │
│     • Configure build & start commands                     │
│     • Select FREE tier                                     │
│                                                             │
│  4. Build Phase (~1 min):                                  │
│     ┌─────────────────────────────────┐                   │
│     │ $ uv sync                        │                   │
│     │   Resolving dependencies...     │                   │
│     │   Installing flask...            │                   │
│     │   Installing gunicorn...         │                   │
│     │   Installing requests...         │                   │
│     │   ✅ Build complete              │                   │
│     └─────────────────────────────────┘                   │
│                                                             │
│  5. Start Phase (~30 sec):                                 │
│     ┌─────────────────────────────────┐                   │
│     │ $ bash render_start.sh          │                   │
│     │   Starting gunicorn...          │                   │
│     │   Workers: 2                    │                   │
│     │   Listening on port 10000       │                   │
│     │   ✅ Service live                │                   │
│     └─────────────────────────────────┘                   │
│                                                             │
│  6. Assigned URL:                                          │
│     🌐 https://scratch-tool-xxxx.onrender.com              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS requests
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  USERS                                                      │
│                                                             │
│  🌐 https://scratch-tool-xxxx.onrender.com                 │
│     ├── /                    (Home page)                   │
│     ├── /document/1259204833 (Document project)           │
│     └── /health              (Health check)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Update Flow (After Initial Deployment)

```
LOCAL MACHINE                    GITHUB                RENDER.COM
     │                             │                       │
     │  git push                   │                       │
     │ ──────────────────────────> │                       │
     │                             │                       │
     │                             │  webhook              │
     │                             │ ───────────────────>  │
     │                             │                       │
     │                             │                   🔄 Auto
     │                             │                   rebuild
     │                             │                       │
     │                             │                   ✅ Deploy
     │                             │                       │
     │                             │                   🌐 Live
     │                             │                       │
```

## 📋 Configuration Summary

### Build Command
```bash
uv sync
```
**What it does**: 
1. Reads your `pyproject.toml` file
2. Resolves all dependencies automatically
3. Creates/updates virtual environment
4. Installs all packages

**Why this is great**:
- ⚡ Uses `uv` (pre-installed on Render)
- 📦 No `requirements.txt` needed
- 🚀 10-100x faster than pip
- ✅ Reads from your existing `pyproject.toml`

### Start Command
```bash
bash render_start.sh
```
**What it does**: Runs the startup script which:
- Sets PORT from environment variable
- Starts Gunicorn with 2 workers
- Binds to 0.0.0.0:$PORT
- Enables logging

### Inside render_start.sh
```bash
#!/bin/bash
PORT=${PORT:-8000}
exec gunicorn main:flask_app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

## 🎯 Service Configuration Table

| Setting | Value | Why? |
|---------|-------|------|
| **Runtime** | Python 3 | Your app is Python |
| **Workers** | 2 | Good for 512MB RAM |
| **Timeout** | 120s | Scratch API can be slow |
| **Port** | $PORT (auto) | Render assigns dynamically |
| **Logging** | stdout/stderr | Visible in Render dashboard |
| **Health Check** | / or /health | Optional monitoring |

## 🚦 Service States

```
🟢 ACTIVE
   ├─ Responding to requests
   ├─ All workers running
   └─ Normal performance

😴 SLEEPING (after 15 min inactivity)
   ├─ Service paused
   ├─ No resource usage
   └─ Wake on next request (~1 min)

🔄 WAKING
   ├─ Service spinning up
   ├─ Loading dependencies
   └─ ~60 seconds to ready

🔴 ERROR
   ├─ Build failed
   ├─ Start failed
   └─ Check logs!
```

## 📈 Free Tier Limits

```
┌──────────────────────────────────────────┐
│  RENDER FREE TIER                        │
├──────────────────────────────────────────┤
│  ⏰ Hours:     750/month                 │
│  💾 RAM:       512 MB                    │
│  💽 Disk:      Free                      │
│  🌐 Bandwidth: 100 GB/month              │
│  🔐 SSL:       ✅ Automatic              │
│  😴 Sleep:     After 15 min              │
│  ⏰ Wake:      ~1 minute                 │
│  🔄 Deploys:   Unlimited                 │
└──────────────────────────────────────────┘

✅ Perfect for: Development, demos, low-traffic apps
⚠️  Not ideal for: 24/7 production, high-traffic sites
```

## 🎨 Example Workflow

### Day 1: Initial Deployment
```bash
# 1. Create deployment files (done ✅)
# 2. Push to GitHub
git push origin master

# 3. Create Web Service on Render
#    → Takes 2-5 minutes
#    → Get URL: https://scratch-tool-xxxx.onrender.com

# 4. Test it!
curl https://scratch-tool-xxxx.onrender.com/
```

### Day 2: Make Updates
```bash
# 1. Edit code
vim main.py

# 2. Commit and push
git add main.py
git commit -m "Add new feature"
git push

# 3. Render auto-deploys! (2-3 min)
# 4. Done! Changes are live
```

## 🔧 Troubleshooting Flow

```
❌ Deployment Failed?
   │
   ├─> Build Error?
   │   └─> Check requirements.txt
   │       • All dependencies listed?
   │       • Correct versions?
   │
   ├─> Start Error?
   │   └─> Check start command
   │       • Correct file name?
   │       • Script executable?
   │       • Using $PORT variable?
   │
   └─> Runtime Error?
       └─> Check logs
           • Import errors?
           • Missing files?
           • API issues?
```

## 🎓 Learning Curve

```
Difficulty:  ⭐ Easy
Time:        5-10 minutes
Steps:       6 simple steps
Automation:  ✅ Yes (auto-deploy)
Cost:        💰 FREE
```

## 📚 Documentation Links

- **This guide**: Step-by-step visual walkthrough
- **[RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)**: Comprehensive deployment guide
- **[RENDER_QUICKSTART.md](RENDER_QUICKSTART.md)**: Quick reference card
- **[DEPLOYMENT.md](DEPLOYMENT.md)**: All deployment options

---

**Ready to deploy?** Follow the steps in [RENDER_QUICKSTART.md](RENDER_QUICKSTART.md)! 🚀
