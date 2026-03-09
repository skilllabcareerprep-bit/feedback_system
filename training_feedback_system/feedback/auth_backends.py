"""
Custom authentication backend with aggressive retry logic for handling database hibernation on Render.
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
    Specifically handles Render's free-tier PostgreSQL hibernation issues with aggressive retries.
    """
    
    MAX_RETRIES = 5
    RETRY_DELAYS = [2, 3, 5, 7, 10]  # Increasing delays in seconds
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate with aggressive retry logic for connection failures.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                # Force database connection reset
                connection.close()
                
                # Try to ping database to wake it from hibernation
                self._ping_database()
                
                # Proceed with normal authentication
                return super().authenticate(request, username=username, password=password, **kwargs)
                
            except Exception as e:
                error_message = str(e)
                
                # Check if it's a connection/SSL error
                if any(keyword in error_message for keyword in ['SSL', 'connection', 'failed', 'closed', 'timeout', 'refused']):
                    delay = self.RETRY_DELAYS[attempt] if attempt < len(self.RETRY_DELAYS) else self.RETRY_DELAYS[-1]
                    logger.warning(f"Database connection attempt {attempt + 1}/{self.MAX_RETRIES} failed: {error_message}. Retrying in {delay}s...")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        # Wait before retrying (increasing delays)
                        time.sleep(delay)
                        # Force connection reset
                        connection.close()
                        continue
                    else:
                        logger.error(f"Authentication failed after {self.MAX_RETRIES} attempts")
                        raise
                else:
                    # Not a connection error (e.g., invalid credentials), raise immediately
                    logger.warning(f"Authentication error (non-connection): {error_message}")
                    raise
    
    def _ping_database(self):
        """
        Ping the database to wake it up from hibernation.
        Uses a simple query to test connectivity.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            logger.info("Database ping successful")
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Database ping failed: {error_msg}")
            raise
