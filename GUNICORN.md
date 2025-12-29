# Running the Server with Gunicorn - Quick Guide

## What is Gunicorn?

Gunicorn (Green Unicorn) is a production-grade Python WSGI HTTP server. It's the recommended way to run Flask applications in production instead of Flask's built-in development server.

## Quick Start

### 1. Install (Already Done)

Gunicorn is already in your dependencies:

```bash
uv sync
```

### 2. Run Server

```bash
# Simple (listens on 127.0.0.1:8000)
uv run gunicorn main:flask_app

# Production (all interfaces, 4 workers)
uv run gunicorn main:flask_app --bind 0.0.0.0:8000 --workers 4

# Using config file
uv run gunicorn main:flask_app -c gunicorn.conf.py
```

### 3. Access

Open browser: `http://localhost:8000` or `http://your-server-ip:8000`

## Common Commands

| Purpose | Command |
|---------|---------|
| Development | `uv run main.py server` |
| Basic production | `uv run gunicorn main:flask_app` |
| Production (recommended) | `uv run gunicorn main:flask_app -b 0.0.0.0:8000 -w 4` |
| With config file | `uv run gunicorn main:flask_app -c gunicorn.conf.py` |
| Custom port | `uv run gunicorn main:flask_app --bind 0.0.0.0:9000` |
| More workers | `uv run gunicorn main:flask_app --workers 8` |
| Longer timeout | `uv run gunicorn main:flask_app --timeout 180` |

## Configuration File

The project includes `gunicorn.conf.py` with production-ready settings:

```bash
# Just run with the config file
uv run gunicorn main:flask_app -c gunicorn.conf.py
```

Key settings:
- **Port**: 8000 (change in config file)
- **Workers**: Auto-calculated based on CPU cores
- **Timeout**: 120 seconds (good for Scratch API calls)
- **Logging**: Enabled to stdout

## Key Options

- `-b, --bind`: Address to bind (e.g., `0.0.0.0:8000`)
- `-w, --workers`: Number of worker processes (default: 1, recommended: 4)
- `--timeout`: Worker timeout in seconds (default: 30, use 120+ for API calls)
- `-c, --config`: Path to config file
- `--access-logfile`: Access log file (`-` for stdout)
- `--error-logfile`: Error log file (`-` for stdout)
- `--log-level`: Log level (debug, info, warning, error, critical)

## Why Gunicorn?

| Feature | Flask Dev Server | Gunicorn |
|---------|------------------|----------|
| **Production Ready** | ❌ No | ✅ Yes |
| **Multiple Workers** | ❌ Single threaded | ✅ Multi-process |
| **Performance** | 🐌 Slow | 🚀 Fast |
| **Reliability** | ❌ Crashes easily | ✅ Worker restart |
| **Security** | ⚠️ Basic | ✅ Production-grade |
| **Use Case** | Development only | Production deployment |

## Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Or with netstat
netstat -tulpn | grep 8000

# Kill the process
kill -9 <PID>
```

### Workers Timing Out

Increase timeout:

```bash
uv run gunicorn main:flask_app --timeout 300
```

### Can't Access from Other Machines

Bind to all interfaces:

```bash
uv run gunicorn main:flask_app --bind 0.0.0.0:8000
```

## Next Steps

- **Behind Nginx**: See [DEPLOYMENT.md](DEPLOYMENT.md#3-behind-nginx-recommended-for-production)
- **Systemd Service**: See [DEPLOYMENT.md](DEPLOYMENT.md#4-systemd-service-linux)
- **Docker**: See [DEPLOYMENT.md](DEPLOYMENT.md#5-docker-deployment)
- **PythonAnywhere**: See [DEPLOYMENT.md](DEPLOYMENT.md#6-pythonanywhere)

## Testing

```bash
# Start server in background
uv run gunicorn main:flask_app --bind 127.0.0.1:8000 --workers 2 &

# Test with curl
curl http://localhost:8000/

# Stop server
pkill -f gunicorn
```

## More Info

- Full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
- Gunicorn docs: https://docs.gunicorn.org/
- Flask deployment: https://flask.palletsprojects.com/en/latest/deploying/
