#!/usr/bin/env python
"""
Initialize admin superuser for the Django application.
This script can be run locally or during deployment on Render.
"""

import os
import sys
import django
from pathlib import Path

# Add project to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'training_feedback_system.settings')

# Set defaults for local development if not in environment
if 'DATABASE_URL' not in os.environ:
    os.environ['DATABASE_URL'] = ''
if 'ALLOWED_HOSTS' not in os.environ:
    os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1'
if 'OPENAI_API_KEY' not in os.environ:
    os.environ['OPENAI_API_KEY'] = 'sk-test'

django.setup()

from django.contrib.auth.models import User

def create_superuser():
    """Create a default superuser"""
    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'Feedback@2026')
    
    # Check if superuser already exists
    if User.objects.filter(is_superuser=True).exists():
        print('✓ Superuser already exists, skipping creation')
        return
    
    try:
        # Delete any existing admin user first
        User.objects.filter(username=username).delete()
        
        # Create superuser
        User.objects.create_superuser(username, email, password)
        print(f'✓ Superuser "{username}" created successfully')
        print(f'✓ Email: {email}')
        print(f'✓ Password: {password}')
    except Exception as e:
        print(f'⚠ Error creating superuser: {str(e)}')

if __name__ == '__main__':
    create_superuser()

