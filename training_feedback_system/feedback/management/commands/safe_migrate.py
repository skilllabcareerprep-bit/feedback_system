"""
Safe migration command that handles database hibernation gracefully.
This is crucial for Render's free-tier PostgreSQL which hibernates after 15 minutes.
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Safe database migrations with retry logic for hibernated databases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retry attempts',
        )
        parser.add_argument(
            '--retry-delay',
            type=int,
            default=5,
            help='Delay in seconds between retries',
        )
        parser.add_argument(
            '--skip-on-error',
            action='store_true',
            help='Skip migrations if database is unavailable (for build servers)',
        )

    def handle(self, *args, **options):
        max_retries = options['max_retries']
        retry_delay = options['retry_delay']
        skip_on_error = options['skip_on_error']

        for attempt in range(max_retries):
            try:
                self.stdout.write(f'Migration attempt {attempt + 1} of {max_retries}...')
                
                # Test connection first
                self._test_connection()
                self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
                
                # Run actual migrations
                call_command('migrate', verbosity=1, interactive=False)
                self.stdout.write(self.style.SUCCESS('✓ Migrations completed successfully'))
                return
                
            except OperationalError as e:
                error_msg = str(e)
                self.stdout.write(self.style.WARNING(f'✗ Connection failed: {error_msg}'))
                
                if 'SSL connection has been closed' in error_msg or 'closed unexpectedly' in error_msg:
                    self.stdout.write(
                        self.style.WARNING(
                            'Database appears to be hibernated (Render free tier). '
                            'Waiting for it to wake up...'
                        )
                    )
                
                if attempt < max_retries - 1:
                    self.stdout.write(f'Retrying in {retry_delay} seconds...')
                    time.sleep(retry_delay)
                else:
                    if skip_on_error:
                        self.stdout.write(
                            self.style.WARNING(
                                'Migration skipped due to repeated failures. '
                                'Database will be migrated when it becomes available.'
                            )
                        )
                        return
                    else:
                        self.stdout.write(self.style.ERROR('✗ Migrations failed after all retries'))
                        raise

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Unexpected error: {str(e)}'))
                raise

    def _test_connection(self):
        """Test database connection"""
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
        except Exception as e:
            logger.error(f'Connection test failed: {str(e)}')
            raise
