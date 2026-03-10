#!/bin/bash
set -e

echo "Running Django migrations..."
python training_feedback_system/manage.py migrate --noinput

echo "Collecting static files..."
python training_feedback_system/manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn training_feedback_system.wsgi:application --workers 1 --timeout 60 --bind 0.0.0.0:10000
