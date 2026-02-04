#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'training_feedback_system.settings')
django.setup()

from django.contrib.auth.models import User

# Only create if no superusers exist
if not User.objects.filter(is_superuser=True).exists():
    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'Feedback@2026')
    
    User.objects.create_superuser(username, email, password)
    print(f'✓ Superuser "{username}" created successfully')
else:
    print('✓ Superuser already exists')
