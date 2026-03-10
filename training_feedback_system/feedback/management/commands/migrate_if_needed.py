from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Run migrations if they have not been run yet'

    def handle(self, *args, **options):
        try:
            # Try to query a table that should exist after migrations
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM auth_user LIMIT 1")
            self.stdout.write(self.style.SUCCESS('Migrations already applied'))
        except Exception as e:
            self.stdout.write(self.style.WARNING('Migrations not applied, running migrate...'))
            try:
                call_command('migrate', verbosity=1)
                self.stdout.write(self.style.SUCCESS('Migrations applied successfully'))
            except Exception as migrate_error:
                self.stdout.write(self.style.ERROR(f'Failed to run migrations: {migrate_error}'))
