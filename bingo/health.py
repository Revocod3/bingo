from django.http import JsonResponse
from django.db import connections
from django.conf import settings
import os
import sys
import django
import socket
import psutil
import logging
import traceback
import datetime
from django.db.utils import OperationalError

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Health check endpoint that diagnoses potential issues
    """
    start_time = datetime.datetime.now()
    health_status = 'ok'
    error_details = []
    
    response = {
        'status': health_status,
        'timestamp': datetime.datetime.now().isoformat(),
        'environment': os.environ.get('ENVIRONMENT', 'unknown'),
        'django_version': django.__version__,
        'python_version': sys.version,
        'hostname': socket.gethostname(),
        'process': {
            'pid': os.getpid(),
        },
        'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set'),
        'database': {},
        'environment_variables': {}
    }
    
    # Add system info
    try:
        memory = psutil.virtual_memory()
        response['system'] = {
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent_used': memory.percent
            },
            'cpu': {
                'percent': psutil.cpu_percent(interval=0.1),
                'count': psutil.cpu_count()
            },
            'disk': {
                'usage': psutil.disk_usage('/').percent
            }
        }
    except Exception as e:
        error_details.append(f"Error getting system info: {str(e)}")
        logger.exception("Error getting system info")
    
    # Check for required environment variables
    required_vars = [
        'DJANGO_SETTINGS_MODULE', 
        'AWS_DB_NAME', 
        'AWS_DB_USER', 
        'AWS_DB_HOST', 
        'AWS_DB_PORT', 
        'AWS_DB_SSL_MODE'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if var != 'AWS_DB_PASSWORD':
            response['environment_variables'][var] = value or 'Not set'
        else:
            response['environment_variables'][var] = '******' if value else 'Not set'
            
        if not value and var != 'AWS_DB_PASSWORD':
            error_details.append(f"Required environment variable {var} not set")
            health_status = 'error'
    
    # Check database connection
    try:
        db_conn = connections['default']
        db_conn.cursor()
        response['database']['connection'] = 'successful'
        
        # Add sanitized database settings
        db_settings = settings.DATABASES['default'].copy()
        if 'PASSWORD' in db_settings:
            db_settings['PASSWORD'] = '******'
        response['database']['settings'] = db_settings
        
        # Check models
        try:
            from bingo.models import Number, Event, BingoCard
            response['database']['models'] = {}
            
            try:
                response['database']['models']['event_count'] = Event.objects.count()
                response['database']['models']['card_count'] = BingoCard.objects.count()
                response['database']['models']['number_count'] = Number.objects.count()
            except Exception as e:
                error_details.append(f"Error querying models: {str(e)}")
                response['database']['models']['error'] = str(e)
                health_status = 'error'
                
        except ImportError as e:
            error_details.append(f"Error importing models: {str(e)}")
            response['database']['models'] = {'error': str(e)}
            health_status = 'error'
            
    except OperationalError as e:
        response['database']['connection'] = 'failed'
        response['database']['error'] = str(e)
        error_details.append(f"Database connection error: {str(e)}")
        health_status = 'error'
        
    except Exception as e:
        response['database']['connection'] = 'failed'
        response['database']['error'] = str(e)
        response['database']['traceback'] = traceback.format_exc()
        error_details.append(f"Unexpected database error: {str(e)}")
        health_status = 'error'
    
    # Update final status
    response['status'] = health_status
    if error_details:
        response['errors'] = error_details
    
    # Calculate response time
    end_time = datetime.datetime.now()
    response['response_time_ms'] = (end_time - start_time).total_seconds() * 1000
    
    logger.info(f"Health check completed with status: {health_status}")
    if health_status == 'error':
        logger.error(f"Health check errors: {error_details}")
    
    return JsonResponse(response)
