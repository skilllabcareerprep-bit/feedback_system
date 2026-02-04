from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Create a default superuser if none exists'

    def handle(self, *args, **options):
        try:
            # Check if superuser already exists
            if User.objects.filter(is_superuser=True).exists():
                self.stdout.write(self.style.SUCCESS('A superuser already exists'))
                return

            # Create default superuser from environment variables
            username = os.getenv('ADMIN_USERNAME', 'admin')
            email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
            password = os.getenv('ADMIN_PASSWORD', 'admin123456')

            User.objects.create_superuser(username, email, password)
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully created superuser "{username}"'
            ))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error: {str(e)}')
