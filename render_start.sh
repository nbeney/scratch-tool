#!/bin/bash
# Start script for Render.com deployment
# This script launches the Gunicorn server with appropriate settings

# Use Render's PORT environment variable (or default to 8000)
# Render automatically sets PORT, so we must listen on it
PORT=${PORT:-8000}

# Start Gunicorn with production settings
# - 2 workers for 512MB RAM (free tier)
# - 120 second timeout for Scratch API calls
# - Log to stdout/stderr for Render logs
# Note: On Render, gunicorn will be in PATH after pip install
exec gunicorn main:flask_app \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
