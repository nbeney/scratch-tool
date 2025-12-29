# Gunicorn configuration file for scratch-tool web server
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
# Recommended: (2 × CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120  # Increased for Scratch API calls
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
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

# Graceful timeout
graceful_timeout = 30

# Maximum requests per worker before restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50
