import logging
from django.http import JsonResponse
from django.db.utils import OperationalError
from .db_utils import ensure_database_connection
import os

logger = logging.getLogger(__name__)

class DatabaseConnectionMiddleware:
    """
    Middleware to ensure database connection is available
    and handle database connection errors gracefully.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization
        logger.info("DatabaseConnectionMiddleware initialized")
        # Log environment details for debugging
        logger.info(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'local')}")
        logger.info(f"DATABASE_URL defined: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        try:
            response = self.get_response(request)
            return response
        except OperationalError as e:
            error_msg = str(e)
            logger.error(f"Database connection error: {error_msg}")
            
            # Log more detailed information for hostname issues
            if "could not translate host name" in error_msg:
                host = error_msg.split('"')[1] if '"' in error_msg else "unknown"
                logger.error(f"Hostname resolution failed for: {host}")
                logger.error("This is likely a DNS resolution issue. Check your database URL configuration.")
                
                # Check environment for debugging
                from django.conf import settings
                db_config = settings.DATABASES.get('default', {})
                logger.error(f"Current DB host setting: {db_config.get('HOST', 'not set')}")
                logger.error(f"Current environment: {os.getenv('ENVIRONMENT', 'not set')}")
            
            # Try to reconnect
            if ensure_database_connection():
                # If reconnection successful, try again
                try:
                    return self.get_response(request)
                except Exception as retry_e:
                    logger.error(f"Error after database reconnection attempt: {str(retry_e)}")
            
            # If all attempts failed, return a proper error response
            return JsonResponse({
                'error': 'Database connection error',
                'message': 'The server is experiencing database issues. Please try again later.'
            }, status=503)  # 503 Service Unavailable
        except Exception as e:
            # Let other exceptions pass through to be handled by Django's exception handling
            logger.error(f"Unexpected error in DatabaseConnectionMiddleware: {str(e)}")
            raise
