import logging
import sys
from django.apps import AppConfig
from django.core.management import call_command
from django.db import connection
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)


class FeedbackConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedback'
    verbose_name = 'Feedback System'

    def ready(self):
        """
        Run when Django app is ready.
        Ensures database migrations are applied even if they failed during build.
        """
        # Only run on web server startup (not during manage.py commands)
        if any(x in sys.argv[0] for x in ['gunicorn', 'runserver']):
            self._ensure_database_ready()

    def _ensure_database_ready(self):
        """Ensure database is properly migrated on application startup"""
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            logger.info('✓ Database connection verified')
            
            # Run pending migrations
            try:
                call_command('migrate', verbosity=0, interactive=False)
                logger.info('✓ Migrations applied successfully')
            except Exception as migrate_error:
                logger.warning(f'⚠ Migration check complete: {str(migrate_error)[:100]}')
                
        except OperationalError as e:
            logger.warning(f'⚠ Database unavailable at startup: {str(e)[:100]}')
        except Exception as e:
            logger.error(f'✗ App ready error: {str(e)[:100]}') 
