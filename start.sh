#!/bin/bash
set -e

# Memory-aggressive Gunicorn configuration for Render free tier (512MB)
PORT=${PORT:-8000}

echo "Starting Gunicorn on port $PORT..."
echo "Memory optimization: preload_app=False, lazy-apps enabled"

cd training_feedback_system

# Use sync worker with aggressive memory settings
exec gunicorn \
  --bind 0.0.0.0:$PORT \
  --workers 1 \
  --threads 1 \
  --worker-class=sync \
  --worker-tmp-dir /dev/shm \
  --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --access-logfile - \
  --error-logfile - \
  training_feedback_system.wsgi:application
