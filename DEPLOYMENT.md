# Deployment Guide

This guide covers different ways to deploy the scratch-tool web server for production use.

## Running with Gunicorn (Production)

Gunicorn is a production-grade WSGI HTTP server for Python web applications.

### Basic Usage

```bash
# Run with Gunicorn (simplest)
uv run gunicorn main:flask_app

# Specify host and port
uv run gunicorn main:flask_app --bind 0.0.0.0:8000

# With multiple workers (recommended for production)
uv run gunicorn main:flask_app --bind 0.0.0.0:8000 --workers 4

# With access logging
uv run gunicorn main:flask_app --bind 0.0.0.0:8000 --workers 4 --access-logfile -
```

### Recommended Production Configuration

```bash
uv run gunicorn main:flask_app \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### Configuration Breakdown

- `main:flask_app` - Module name (main.py) and Flask app variable name
- `--bind 0.0.0.0:8000` - Listen on all interfaces, port 8000
- `--workers 4` - Number of worker processes (2-4 × CPU cores recommended)
- `--worker-class sync` - Worker type (sync for CPU-bound tasks)
- `--timeout 120` - Worker timeout in seconds (increase for slow API calls)
- `--access-logfile -` - Log access to stdout
- `--error-logfile -` - Log errors to stdout
- `--log-level info` - Logging verbosity

### Using a Configuration File

Create `gunicorn.conf.py`:

```python
# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "scratch-tool"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for better memory usage
preload_app = True
```

Then run:

```bash
uv run gunicorn main:flask_app -c gunicorn.conf.py
```

## Deployment Options

### 1. Local Development

Use the built-in Flask development server (not for production):

```bash
uv run main.py server --port 5000 --host 127.0.0.1
```

### 2. Production Server with Gunicorn

```bash
uv run gunicorn main:flask_app --bind 0.0.0.0:8000 --workers 4
```

Access at: `http://your-server:8000`

### 3. Behind Nginx (Recommended for Production)

**Nginx configuration** (`/etc/nginx/sites-available/scratch-tool`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Request size limits (for large projects)
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts (for slow API calls)
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Static files (if you add any)
    location /static/ {
        alias /path/to/scratch-tool/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/scratch-tool /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Systemd Service (Linux)

Create `/etc/systemd/system/scratch-tool.service`:

```ini
[Unit]
Description=Scratch Tool Web Server
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/scratch-tool
Environment="PATH=/path/to/scratch-tool/.venv/bin"
ExecStart=/path/to/scratch-tool/.venv/bin/gunicorn main:flask_app \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl start scratch-tool
sudo systemctl enable scratch-tool
sudo systemctl status scratch-tool
```

### 5. Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY models/ models/
COPY scratchblocks_converter.py .

# Install dependencies
RUN uv sync --no-dev

# Expose port
EXPOSE 8000

# Run with Gunicorn
CMD ["uv", "run", "gunicorn", "main:flask_app", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

Build and run:

```bash
docker build -t scratch-tool .
docker run -p 8000:8000 scratch-tool
```

### 6. PythonAnywhere

See [PYTHONANYWHERE.md](PYTHONANYWHERE.md) for detailed instructions.

PythonAnywhere uses WSGI directly (no Gunicorn needed). Configure the WSGI file to point to `main.flask_app`.

## Performance Tuning

### Worker Count

```bash
# CPU-bound tasks (Scratch API calls, HTML generation)
workers = (2 × CPU_cores) + 1

# Example for 4 cores:
--workers 9
```

### Timeout

```bash
# Increase for slow Scratch API responses
--timeout 180  # 3 minutes
```

### Worker Class

```bash
# Sync workers (default, good for CPU-bound)
--worker-class sync

# Async workers (for I/O-bound, more concurrent requests)
--worker-class gevent --worker-connections 1000
# Note: Requires gevent: pip install gevent
```

## Monitoring

### Health Check Endpoint

Add to `main.py` (after the flask_app routes):

```python
@flask_app.route("/health")
def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}, 200
```

### Logging

View Gunicorn logs:

```bash
# If using systemd
sudo journalctl -u scratch-tool -f

# If running in terminal
# Logs appear in stdout/stderr
```

### Process Management

```bash
# Graceful reload (reload code without downtime)
kill -HUP <gunicorn_master_pid>

# Or with systemd
sudo systemctl reload scratch-tool
```

## Environment Variables

Create `.env` file:

```bash
FLASK_ENV=production
SCRATCH_API_TIMEOUT=30
MAX_WORKERS=4
PORT=8000
```

Load in Gunicorn config:

```python
from dotenv import load_dotenv
load_dotenv()
```

## Security Considerations

1. **Never use Flask's dev server in production** - Use Gunicorn instead
2. **Use HTTPS** - Set up SSL/TLS with Let's Encrypt
3. **Rate limiting** - Add rate limiting to prevent abuse
4. **Firewall** - Only expose necessary ports
5. **Keep dependencies updated** - Regularly update packages

## Troubleshooting

### Port already in use

```bash
# Find process using port 8000
lsof -i :8000
# Or
netstat -tulpn | grep 8000

# Kill it
kill -9 <pid>
```

### Workers timing out

Increase timeout:

```bash
--timeout 300  # 5 minutes
```

### Out of memory

Reduce workers:

```bash
--workers 2  # Fewer workers use less memory
```

### Import errors

Ensure working directory is correct:

```bash
cd /path/to/scratch-tool
uv run gunicorn main:flask_app
```

## Quick Reference

| Use Case | Command |
|----------|---------|
| Development | `uv run main.py server` |
| Production (simple) | `uv run gunicorn main:flask_app` |
| Production (recommended) | `uv run gunicorn main:flask_app -b 0.0.0.0:8000 -w 4` |
| With config file | `uv run gunicorn main:flask_app -c gunicorn.conf.py` |
| Behind Nginx | `uv run gunicorn main:flask_app -b 127.0.0.1:8000 -w 4` |
| Docker | `docker run -p 8000:8000 scratch-tool` |

## Additional Resources

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Flask Deployment Options](https://flask.palletsprojects.com/en/latest/deploying/)
- [Nginx Configuration](https://nginx.org/en/docs/)
