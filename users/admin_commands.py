import io
from django.core.management import call_command
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAdminUser])
def run_management_command(request):
    """
    Endpoint that allows running specific management commands.
    Only accessible by admin users.
    """
    command_name = request.data.get('command')
    arguments = request.data.get('args', [])
    options = request.data.get('options', {})
    
    allowed_commands = ['fix_database_columns', 'fix_migrations', 'check_migrations']
    
    if not command_name:
        return Response({"error": "Command name is required"}, status=400)
    
    if command_name not in allowed_commands:
        return Response({"error": f"Command not allowed. Allowed commands: {', '.join(allowed_commands)}"}, status=400)
    
    # Capture command output
    output = io.StringIO()
    try:
        call_command(command_name, *arguments, **options, stdout=output)
        return Response({"success": True, "output": output.getvalue()})
    except Exception as e:
        return Response({"success": False, "error": str(e), "output": output.getvalue()}, status=500)
