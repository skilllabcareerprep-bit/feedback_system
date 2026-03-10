"""
Custom authentication backend with aggressive retry logic for handling database connection failures on Render.
Simplified to avoid pinging which causes SSL reconnection issues on free tier.
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
    Specifically handles Render's free-tier PostgreSQL connection drops.
    
    CRITICAL: Does NOT ping database before retrying - pinging causes SSL reconnection 
    issues on free tier. Instead, relies on connection recycling via reduced CONN_MAX_AGE.
    """
    
    MAX_RETRIES = 5  # Increased for free tier stability
    RETRY_DELAYS = [2, 3, 4, 5, 6]  # Much longer delays - give Render time to recover SSL
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate with retry logic for connection failures.
        Avoids database pinging which triggers SSL errors on Render free tier.
        """
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Reset stale connection before each retry attempt
                connection.close()
                
                # Proceed with normal authentication
                return super().authenticate(request, username=username, password=password, **kwargs)
                
            except Exception as e:
                last_exception = e
                error_message = str(e)
                
                # Check if it's a connection/SSL error worth retrying
                if any(keyword in error_message.lower() for keyword in 
                       ['ssl', 'connection', 'failed', 'closed', 'timeout', 'refused', 'operational']):
                    
                    if attempt < self.MAX_RETRIES - 1:
                        delay = self.RETRY_DELAYS[attempt]
                        logger.warning(
                            f"Database connection attempt {attempt + 1}/{self.MAX_RETRIES} failed: {error_message}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Authentication failed after {self.MAX_RETRIES} connection retry attempts. "
                            f"Last error: {error_message}"
                        )
                else:
                    # Not a connection error (e.g., invalid credentials), raise immediately
                    logger.debug(f"Non-connection authentication error: {error_message}")
                    raise
        
        # If all retries exhausted, raise the last exception
        if last_exception:
            raise last_exception

