import time
import logging
from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings
import socket

logger = logging.getLogger(__name__)

def ensure_database_connection():
    """
    Attempts to establish a connection to the database with retries.
    Returns True if successful, False otherwise.
    """
    max_attempts = getattr(settings, 'DATABASE_RETRY_ATTEMPTS', 3)
    retry_delay = getattr(settings, 'DATABASE_RETRY_DELAY', 1)
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Try to establish a database connection
            connections['default'].ensure_connection()
            logger.info("Database connection established successfully")
            return True
        except OperationalError as e:
            logger.warning(f"Database connection attempt {attempt}/{max_attempts} failed: {str(e)}")
            # If this is a DNS resolution error, log more details
            if "could not translate host name" in str(e):
                try:
                    # Try to resolve the hostname to help diagnose DNS issues
                    db_host = settings.DATABASES['default']['HOST']
                    logger.error(f"DNS resolution failed for database host: {db_host}")
                    try:
                        # Try to manually resolve the hostname
                        ip = socket.gethostbyname(db_host)
                        logger.info(f"Manual DNS resolution: {db_host} resolves to {ip}")
                    except socket.gaierror as dns_error:
                        logger.error(f"Manual DNS resolution failed: {str(dns_error)}")
                except Exception as inner_e:
                    logger.error(f"Error during hostname resolution check: {str(inner_e)}")
            
            if attempt < max_attempts:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All database connection attempts failed.")
                return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to database: {str(e)}")
            return False
    
    return False
