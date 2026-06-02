#!/bin/bash
set -e

# Ensure PORT is set (Render provides this)
PORT=${PORT:-8000}

echo "Starting Gunicorn on port $PORT..."
cd training_feedback_system

exec gunicorn \
  --bind 0.0.0.0:$PORT \
  --workers 1 \
  --threads 1 \
  --worker-class=sync \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  training_feedback_system.wsgi:application
