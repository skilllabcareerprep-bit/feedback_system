import os
import sys
import django

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'training_feedback_system.settings')
os.environ['DEBUG'] = 'False'
os.environ['DATABASE_URL'] = ''
os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1'
os.environ['OPENAI_API_KEY'] = 'dummy'

django.setup()

from django.contrib.auth.models import User
from django.db import connection

# Use SQLite for local testing
connection.settings_dict['ENGINE'] = 'django.db.backends.sqlite3'
connection.settings_dict['NAME'] = 'db.sqlite3'

# Delete old admin user if exists
User.objects.filter(username='admin').delete()
print("✓ Deleted old admin user")

# Create new superuser
user = User.objects.create_superuser(
    username='admin',
    email='admin@skilllab.com',
    password='Feedback@2026'
)
print("✓ Superuser 'admin' created successfully!")
print("✓ Password: Feedback@2026")
