import logging
from django.http import JsonResponse
from django.db.utils import OperationalError, ProgrammingError
from .db_utils import ensure_database_connection
import os
import traceback
import json
from django.utils.deprecation import MiddlewareMixin
from rest_framework.response import Response

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
        logger.info(
            f"DATABASE_URL defined: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")

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
                host = error_msg.split(
                    '"')[1] if '"' in error_msg else "unknown"
                logger.error(f"Hostname resolution failed for: {host}")
                logger.error(
                    "This is likely a DNS resolution issue. Check your database URL configuration.")

                # Check environment for debugging
                from django.conf import settings
                db_config = settings.DATABASES.get('default', {})
                logger.error(
                    f"Current DB host setting: {db_config.get('HOST', 'not set')}")
                logger.error(
                    f"Current environment: {os.getenv('ENVIRONMENT', 'not set')}")

            # Try to reconnect
            if ensure_database_connection():
                # If reconnection successful, try again
                try:
                    return self.get_response(request)
                except Exception as retry_e:
                    logger.error(
                        f"Error after database reconnection attempt: {str(retry_e)}")

            # If all attempts failed, return a proper error response
            return JsonResponse({
                'error': 'Database connection error',
                'message': 'The server is experiencing database issues. Please try again later.'
            }, status=503)  # 503 Service Unavailable
        except ProgrammingError as e:
            # Log database schema errors (like missing tables)
            error_msg = str(e)
            logger.error(f"Database schema error: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Return detailed error for debugging
            if os.environ.get('DEBUG', 'False') == 'True':
                return JsonResponse({
                    'error': 'Database schema error',
                    'message': error_msg,
                    'traceback': traceback.format_exc()
                }, status=500)
            else:
                return JsonResponse({
                    'error': 'Database schema error',
                    'message': 'The application database schema is not correctly set up.'
                }, status=500)
        except Exception as e:
            # Let other exceptions pass through to be handled by Django's exception handling
            logger.error(
                f"Unexpected error in DatabaseConnectionMiddleware: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise


# Dictionary of common error messages translations (English to Spanish)
ERROR_TRANSLATIONS = {
    # Authentication errors
    "Authentication credentials were not provided.": "No se proporcionaron credenciales de autenticación.",
    "Invalid token.": "Token inválido.",
    "Token is invalid or expired": "El token es inválido o ha expirado.",
    "Unable to log in with provided credentials.": "No se puede iniciar sesión con las credenciales proporcionadas.",
    "Invalid password.": "Contraseña inválida.",
    "User account is disabled.": "La cuenta de usuario está deshabilitada.",
    "This password is too common.": "Esta contraseña es demasiado común.",
    "This password is too short.": "Esta contraseña es demasiado corta.",
    "The two password fields didn't match.": "Los dos campos de contraseña no coinciden.",
    "Invalid email/password.": "Email o contraseña inválidos.",
    "User with this Email already exists.": "Ya existe un usuario con este correo electrónico.",
    "Email is not verified.": "El correo electrónico no está verificado.",
    "A user is already registered with this e-mail address.": "Ya hay un usuario registrado con esta dirección de correo electrónico.",

    # Permission errors
    "You do not have permission to perform this action.": "No tienes permisos para realizar esta acción.",
    "Permission denied.": "Permiso denegado.",

    # Database errors
    "Database connection error": "Error de conexión a la base de datos",
    "The server is experiencing database issues. Please try again later.": "El servidor está experimentando problemas con la base de datos. Por favor, inténtalo más tarde.",
    "Database schema error": "Error en el esquema de la base de datos",
    "The application database schema is not correctly set up.": "El esquema de la base de datos de la aplicación no está configurado correctamente.",

    # Resource errors
    "Not found.": "No encontrado.",
    "No se ha encontrado.": "No se ha encontrado.",
    "Method not allowed.": "Método no permitido.",

    # Generic errors
    "An error occurred.": "Ha ocurrido un error.",
    "Bad request.": "Solicitud incorrecta.",
    "Invalid request.": "Solicitud inválida.",
    "Server error.": "Error del servidor.",
    "Internal server error.": "Error interno del servidor.",
    "Service temporarily unavailable.": "Servicio temporalmente no disponible.",

    # Field validation errors
    "This field is required.": "Este campo es obligatorio.",
    "This field may not be blank.": "Este campo no puede estar en blanco.",
    "This field may not be null.": "Este campo no puede ser nulo.",
    "Invalid input.": "Entrada inválida.",
    "Enter a valid email address.": "Ingresa una dirección de correo electrónico válida.",
    "Enter a valid value.": "Ingresa un valor válido.",
    "Ensure this value is less than or equal to": "Asegúrate de que este valor sea menor o igual a",
    "Ensure this value is greater than or equal to": "Asegúrate de que este valor sea mayor o igual a",
    "Ensure this field has no more than": "Asegúrate de que este campo no tenga más de",
    "Ensure this field has at least": "Asegúrate de que este campo tenga al menos",
}


class ErrorTranslationMiddleware:
    """
    Middleware to translate error messages from English to Spanish
    in JSON responses from views and REST framework.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        logger.info("ErrorTranslationMiddleware initialized")

    def __call__(self, request):
        response = self.get_response(request)

        # Only process JSON responses with error status codes (4xx, 5xx)
        if (400 <= response.status_code < 600 and
                'application/json' in response.get('Content-Type', '')):

            try:
                # Try to decode the response content
                if hasattr(response, 'content'):
                    content = json.loads(response.content.decode('utf-8'))

                    # Translate error messages
                    translated_content = self._translate_response(content)

                    # Update the response with translated content
                    if translated_content != content:
                        response.content = json.dumps(
                            translated_content).encode('utf-8')

                # Handle DRF Response objects
                elif isinstance(response, Response):
                    translated_data = self._translate_response(response.data)
                    if translated_data != response.data:
                        response.data = translated_data
                        response._is_rendered = False
                        response.render()

            except (json.JSONDecodeError, UnicodeDecodeError, AttributeError) as e:
                logger.error(
                    f"Error processing response in ErrorTranslationMiddleware: {str(e)}")

        return response

    def _translate_response(self, content):
        """Recursively translate error messages in the response content"""
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, str) and value in ERROR_TRANSLATIONS:
                    content[key] = ERROR_TRANSLATIONS[value]
                elif isinstance(value, (dict, list)):
                    content[key] = self._translate_response(value)
                # Handle partial string matches
                elif isinstance(value, str):
                    for eng, spa in ERROR_TRANSLATIONS.items():
                        if eng in value:
                            content[key] = value.replace(eng, spa)

        elif isinstance(content, list):
            for i, item in enumerate(content):
                content[i] = self._translate_response(item)

        return content
