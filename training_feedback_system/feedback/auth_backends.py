"""
Custom authentication backend with retry logic for handling database hibernation on Render.
"""
import time
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import connection

logger = logging.getLogger(__name__)

User = get_user_model()


class RetryAuthenticationBackend(ModelBackend):
    """
    Custom backend that retries authentication on database connection failures.
    Specifically handles Render's free-tier PostgreSQL hibernation issues.
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate with retry logic for connection failures.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # Try to wake up the database with a simple ping
                self._ping_database()
                
                # Proceed with normal authentication
                return super().authenticate(request, username=username, password=password, **kwargs)
                
            except Exception as e:
                error_message = str(e)
                
                # Check if it's a connection error
                if any(keyword in error_message for keyword in ['SSL', 'connection', 'failed', 'closed']):
                    logger.warning(f"Database connection attempt {attempt + 1}/{self.MAX_RETRIES} failed: {error_message}")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        # Wait before retrying
                        time.sleep(self.RETRY_DELAY)
                        # Reset the connection
                        connection.close()
                        continue
                    else:
                        logger.error(f"Authentication failed after {self.MAX_RETRIES} attempts")
                        raise
                else:
                    # Not a connection error, raise immediately
                    raise
    
    def _ping_database(self):
        """
        Ping the database to wake it up from hibernation.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("Database ping successful")
        except Exception as e:
            logger.warning(f"Database ping attempt failed: {str(e)}")
            raise
