# Auto-Deploy on Render.com

Render.com automatically deploys your app whenever you push to your connected GitHub branch. Here's how it works and how to configure it.

## 🔄 How Auto-Deploy Works

```
┌──────────────┐         ┌──────────┐         ┌──────────────┐
│  Local Code  │  push   │  GitHub  │ webhook │  Render.com  │
│              │ ──────> │          │ ──────> │              │
│  git push    │         │  master  │         │  Auto-build  │
└──────────────┘         └──────────┘         └──────────────┘
                                                       │
                                                       │ deploy
                                                       ▼
                                              ┌──────────────┐
                                              │  Live App    │
                                              │  Updated!    │
                                              └──────────────┘
```

## ✅ Auto-Deploy is Enabled by Default!

When you create a Web Service on Render and connect it to a GitHub repository:
- ✅ **Auto-deploy is ON by default**
- ✅ Watches your selected branch (e.g., `master`)
- ✅ Deploys automatically on every push
- ✅ Shows build progress in real-time

## 🎯 Setup Steps

### 1. Connect Your Repository

When creating your Web Service on Render:

1. Click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Select your GitHub account
4. Choose `scratch-tool` repository
5. Select branch: `master` (or your main branch)

✅ **Auto-deploy is now configured!**

### 2. Verify Auto-Deploy Settings

To check if auto-deploy is enabled:

1. Go to your service in Render Dashboard
2. Click **"Settings"** in the left sidebar
3. Look for **"Auto-Deploy"** section
4. Should show: **"Auto-Deploy: Yes"**

## 📊 Auto-Deploy Behavior

### What Triggers a Deploy?

✅ **Triggers automatic deployment:**
- `git push origin master` (or your configured branch)
- Merging a pull request to your branch
- Any commit pushed to the watched branch

❌ **Does NOT trigger deployment:**
- Pushing to other branches
- Creating a branch
- Opening a pull request (without merging)
- Commits to forks

### Deploy Process

```
1. You push code to GitHub
   ↓
2. GitHub sends webhook to Render
   ↓
3. Render detects the change (within seconds)
   ↓
4. Render starts build automatically
   ├── Status: "Building..."
   ├── Runs: uv sync
   └── Duration: ~1-2 minutes
   ↓
5. Build completes
   ↓
6. Render deploys new version
   ├── Starts: bash render_start.sh
   ├── Health check passes
   └── Status: "Live"
   ↓
7. Your app is updated! (zero-downtime)
```

## 🔧 Configuration Options

### Enable/Disable Auto-Deploy

In Render Dashboard → Your Service → **Settings**:

**To disable auto-deploy:**
1. Find **"Auto-Deploy"** section
2. Click **"Turn off auto-deploy"**
3. You'll need to deploy manually from now on

**To enable auto-deploy:**
1. Find **"Auto-Deploy"** section
2. Click **"Turn on auto-deploy"**
3. Future pushes will auto-deploy

### Change Watched Branch

1. Go to **Settings**
2. Find **"Branch"** setting
3. Change to your desired branch (e.g., `main`, `production`)
4. Click **"Save Changes"**

## 📝 Testing Auto-Deploy

### Quick Test

```bash
# 1. Make a small change
echo "# Test auto-deploy" >> README.md

# 2. Commit and push
git add README.md
git commit -m "Test auto-deploy"
git push origin master

# 3. Watch in Render Dashboard
# Go to your service → Events tab
# You should see "Deploy triggered by push to master"
```

### What You'll See

**In Render Dashboard:**
```
Events Tab:
┌────────────────────────────────────────────┐
│ Deploy triggered by push to master         │
│ Status: Building...                        │
│ Commit: abc1234 "Test auto-deploy"        │
│ Started: 2 seconds ago                     │
└────────────────────────────────────────────┘
```

**In Logs Tab:**
```
[Build]
Running: uv sync
Resolving dependencies...
Installing packages...
✓ Build complete

[Deploy]
Running: bash render_start.sh
Starting gunicorn...
✓ Service is live
```

## 🚀 Typical Workflow

### Development Cycle with Auto-Deploy

```bash
# 1. Make changes locally
vim main.py

# 2. Test locally (optional)
uv run main.py server

# 3. Commit your changes
git add main.py
git commit -m "Add new feature"

# 4. Push to GitHub
git push origin master

# 5. Render automatically:
#    - Detects the push (within seconds)
#    - Starts building (~1-2 min)
#    - Deploys new version
#    - Your site is updated!

# 6. Check the deployment
#    - Go to Render Dashboard → Events
#    - Or visit your live URL
```

## ⚙️ Advanced: Deploy Hooks

### Manual Deploy (Override Auto-Deploy)

You can still manually trigger deploys even with auto-deploy enabled:

1. Go to Render Dashboard → Your Service
2. Click **"Manual Deploy"** button (top right)
3. Select **"Deploy latest commit"**
4. Or select **"Clear build cache & deploy"** (if having issues)

### Deploy from API

Render provides a Deploy Hook URL for programmatic deploys:

1. Go to **Settings** → **Deploy Hook**
2. Copy the webhook URL
3. Trigger deploy via HTTP POST:

```bash
curl -X POST https://api.render.com/deploy/srv-xxxxx?key=xxxxx
```

### Deploy from CI/CD

Use the Deploy Hook in GitHub Actions, GitLab CI, etc.:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Render
on:
  push:
    branches: [master]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

## 📊 Monitoring Auto-Deploys

### Events Tab

See all deployments:
1. Go to your service
2. Click **"Events"** tab
3. View deploy history with:
   - Commit message
   - Author
   - Status (Success/Failed)
   - Duration
   - Timestamp

### Notifications

Get notified of deployments:
1. Go to **Settings** → **Notifications**
2. Add email notifications for:
   - Deploy started
   - Deploy succeeded
   - Deploy failed

### Slack Integration

Connect to Slack:
1. Go to **Settings** → **Notifications**
2. Click **"Add to Slack"**
3. Choose your Slack channel
4. Approve permissions

You'll get messages like:
```
🚀 scratch-tool: Deploy started
   Commit: "Add new feature" by @username
   
✅ scratch-tool: Deploy succeeded (1m 23s)
   https://scratch-tool-xxxx.onrender.com
```

## 🔒 Security Considerations

### Branch Protection

Protect your production branch:

**In GitHub:**
1. Go to repository **Settings** → **Branches**
2. Add rule for `master` branch
3. Enable:
   - ✅ Require pull request reviews
   - ✅ Require status checks
   - ✅ Require branches to be up to date

This prevents direct pushes and requires PRs to merge.

### Deployment Previews

For testing before production (paid plans):
1. Enable **Preview Environments**
2. Each PR gets its own temporary URL
3. Test changes before merging
4. Auto-deleted when PR closes

## 🐛 Troubleshooting

### Auto-Deploy Not Working

**Problem**: Pushed to GitHub but Render didn't deploy

**Solutions:**

1. **Check GitHub connection:**
   - Settings → GitHub → "Reconnect"
   
2. **Check branch name:**
   - Settings → Branch → Verify it matches your push

3. **Check GitHub webhook:**
   - GitHub repo → Settings → Webhooks
   - Should see Render webhook with recent deliveries
   - Click webhook → "Recent Deliveries"
   - Should show successful delivery

4. **Re-authorize GitHub:**
   - Settings → GitHub Integration
   - Click "Re-authorize"

### Deploy Stuck

**Problem**: Build is running but seems stuck

**Solutions:**

1. **Check build logs:**
   - Logs tab → Look for errors

2. **Cancel and retry:**
   - Click "Cancel Build"
   - Click "Manual Deploy"

3. **Clear build cache:**
   - Manual Deploy → "Clear build cache & deploy"

### Failed Deploys

**Problem**: Build or deploy fails

**Check:**

1. **Build logs** for errors
2. **Dependencies** in pyproject.toml
3. **Build command** is correct: `uv sync`
4. **Start command** is correct: `bash render_start.sh`

## ✅ Best Practices

### 1. Use Feature Branches

```bash
# Create feature branch
git checkout -b feature/new-feature

# Work and commit
git add .
git commit -m "Add feature"

# Push to GitHub (won't trigger deploy)
git push origin feature/new-feature

# Create PR, review, then merge to master
# Only then will Render auto-deploy
```

### 2. Test Before Pushing

```bash
# Test locally first
uv run main.py server

# Run tests
uv run pytest

# Then push
git push origin master
```

### 3. Use Meaningful Commit Messages

```bash
# Good ✅
git commit -m "Fix: Resolve timeout issue on /document route"

# Bad ❌
git commit -m "fix stuff"
```

These messages appear in Render's Events tab!

### 4. Monitor First Deploy

After pushing:
1. Watch Events tab
2. Check Logs for errors
3. Visit your live site
4. Test the changes

## 📋 Quick Reference

| Action | Command | Result |
|--------|---------|--------|
| **Enable auto-deploy** | Render Settings → Turn on | ✅ Auto-deploy on push |
| **Disable auto-deploy** | Render Settings → Turn off | ⭕ Manual deploy only |
| **Trigger deploy** | `git push origin master` | 🚀 Auto-deploy starts |
| **Manual deploy** | Dashboard → Manual Deploy | 🔧 Deploy without push |
| **View history** | Events tab | 📊 See all deploys |
| **View logs** | Logs tab | 📝 See build output |

## Summary

✅ **Auto-deploy is ON by default** when you connect a GitHub repo

✅ **To deploy**: Just `git push origin master`

✅ **Deploy happens automatically** within seconds of your push

✅ **View progress** in Render Dashboard → Events and Logs tabs

✅ **Zero configuration needed** - it just works!

---

**Your workflow**: Code → Commit → Push → ☕ (Render does the rest!)
