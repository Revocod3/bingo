import os
import sys
import django
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import traceback

@csrf_exempt
def debug_info(request):
    """
    Endpoint that returns detailed debug information.
    Only enabled when DEBUG_ENDPOINT=True environment variable is set.
    """
    # Only allow this endpoint if explicitly enabled
    if os.environ.get('DEBUG_ENDPOINT', 'False') != 'True':
        return JsonResponse({'error': 'Debug endpoint not enabled'}, status=403)
    
    debug_info = {
        'environment': os.environ.get('ENVIRONMENT', 'unknown'),
        'django_version': django.__version__,
        'python_version': sys.version,
        'settings_module': os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set'),
        'database': {},
        'installed_apps': [],
        'tables': [],
    }
    
    # Get installed apps
    try:
        from django.conf import settings
        debug_info['installed_apps'] = settings.INSTALLED_APPS
    except Exception as e:
        debug_info['installed_apps_error'] = str(e)
    
    # Check tables
    try:
        with connection.cursor() as cursor:
            # Check if users_customuser exists
            cursor.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables 
                   WHERE table_schema = 'public'
                   AND table_name = 'users_customuser'
                );
            """)
            debug_info['database']['users_customuser_exists'] = cursor.fetchone()[0]
            
            # List all tables
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            debug_info['tables'] = [table[0] for table in cursor.fetchall()]
            
            # Check migrations
            cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name;")
            debug_info['migrations'] = [f"{app}: {name}" for app, name in cursor.fetchall()]
    except Exception as e:
        debug_info['database_error'] = str(e)
        debug_info['traceback'] = traceback.format_exc()
    
    return JsonResponse(debug_info)
