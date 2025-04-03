"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-clave-local')

# Get environment - default to 'local' if not specified
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Only temporarily to see error details!

ALLOWED_HOSTS = ['*']

import dj_database_url

# Application definition

INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # Required for allauth
    
    # Swagger
    'drf_spectacular',
    
    # REST Framework
    'rest_framework',
    'rest_framework.authtoken',
    
    # Authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.google',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'corsheaders',  # Add this line
    
    # Project apps
    'users',
    'bingo',
    'core',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  
    'core.middleware.DatabaseConnectionMiddleware', 
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', 
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'bingo', 'templates'),  # Añadir esta línea
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
postgres_pswd = os.getenv('LOCAL_POSTGRESS_PSWD')
# Get environment - default to 'local' if not specified
ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')

# Add database retry and timeout settings
DATABASE_RETRY_ATTEMPTS = 3
DATABASE_RETRY_DELAY = 1  # seconds
DATABASE_TIMEOUT = 20  # seconds

# First check for direct DATABASE_URL environment variable (highest priority)
database_url = os.getenv('DATABASE_URL')
if database_url:
    DATABASES = {
        'default': dj_database_url.parse(database_url)
    }
    # Ensure we have proper connection settings
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': DATABASE_TIMEOUT,
        'keepalives': 1,
        'keepalives_idle': 30,
        'keepalives_interval': 10,
        'keepalives_count': 5,
        'sslmode': os.getenv('DB_SSL_MODE', 'prefer'),
    }
    # Log the database host for debugging
    print(f"Using database URL with host: {DATABASES['default'].get('HOST', 'unknown')}")
else:
    # Local development database configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            # 'NAME': 'bingo',
            # 'USER': 'bingouser',
            # 'PASSWORD': postgres_pswd,
            # 'HOST': 'localhost',
            # 'PORT': '5432',
            'NAME': os.environ.get('DATABASE_NAME'),
            'USER': os.environ.get('DATABASE_USER'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD'),
            'HOST': os.environ.get('DATABASE_HOST'),
            'PORT': os.environ.get('DATABASE_PORT'),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
AUTH_USER_MODEL = 'users.CustomUser'

AUTHENTICATION_BACKENDS = [
    'users.auth_backends.EmailVerificationBackend',  # Custom backend that checks email verification
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',  # Changed to HTTP_AUTHORIZATION
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'users.auth_backends.CustomTokenObtainPairSerializer',  # Use our custom serializer
}
REST_USE_JWT = True
JWT_AUTH_COOKIE = 'bingo-app-auth'
JWT_AUTH_REFRESH_COOKIE = 'bingo-app-refresh-token'

# django-allauth settings
SITE_ID = 1
ACCOUNT_USER_MODEL_USERNAME_FIELD = None # Use email for login
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'

# Update these settings based on BYPASS_EMAIL_VERIFICATION
BYPASS_EMAIL_VERIFICATION = os.getenv('BYPASS_EMAIL_VERIFICATION', 'False') == 'True'

# Set these conditionally based on bypass setting
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True

# Additional settings for dj-rest-auth
REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'bingo-app-auth',  # Match this with JWT_AUTH_COOKIE above
    'JWT_AUTH_REFRESH_COOKIE': 'bingo-app-refresh-token',  # Match this with JWT_AUTH_REFRESH_COOKIE above
    'USER_DETAILS_SERIALIZER': 'users.serializers.UserSerializer',
}

# Custom adapter settings
ACCOUNT_ADAPTER = 'users.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'

# Email settings - modify with your actual SMTP settings
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')  
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'revocode222@gmail.com')

# Development settings
BYPASS_EMAIL_VERIFICATION = os.getenv('BYPASS_EMAIL_VERIFICATION', 'False') == 'True'

# Social authentication providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        },
        'AUTH_PARAMS': {
            'access_type': 'online'
        },
        'SCOPE': [
            'profile',
            'email'
        ],
    },
    'facebook': {
        'METHOD': 'oauth2',
        'APP': {
            'client_id': os.getenv('FACEBOOK_CLIENT_ID', ''),
            'secret': os.getenv('FACEBOOK_CLIENT_SECRET', ''),
            'key': ''
        },
        'SCOPE': [
            'email',
            'public_profile'
        ],
    }
}

SOCIALACCOUNT_EMAIL_VERIFICATION = "none"
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_AUTO_SIGNUP = True


CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

# Define base URLs without trailing slashes to avoid CORS errors
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://bingo-frontend-git-main-kev2693s-projects.vercel.app",
    "https://bingo-frontend.vercel.app",
    "https://bingo-api-94i2.onrender.com",
    "https://bingo-frontend-three.vercel.app",
    # Add any new frontend URLs here
]

# Ensure no trailing slashes in any of the URLs
CORS_ALLOWED_ORIGINS = [url.rstrip('/') for url in CORS_ALLOWED_ORIGINS]

# Add CSRF trusted origins
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
]

# Spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'BINGO API',
    'DESCRIPTION': 'API for the Bingo application with user authentication and game management',
    'VERSION': '1.0.0',
    'SECURITY': [{'Bearer': []}],
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter your JWT token in the format: `Bearer <token>`'
        }
    },
    'SERVE_INCLUDE_SCHEMA': True,
    'SERVE_URLCONF': 'core.urls',
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'displayOperationId': True,
        'filter': True,
    },
    'SCHEMA_PATH_PREFIX': '/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_SPLIT_RESPONSE': True,
    'ENUM_NAME_OVERRIDES': {
        'ValidationErrorEnum': 'rest_framework.serializers.ValidationError',
    },
    'PREPROCESSING_HOOKS': [],
    'POSTPROCESSING_HOOKS': [],
}

# Channels configuration
ASGI_APPLICATION = 'core.asgi.application'

# Redis configuration based on environment
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = os.environ.get('REDIS_PORT', '6379')
redis_db = os.environ.get('REDIS_DB', '0')
redis_url = os.environ.get('REDIS_URL', f'redis://{redis_host}:{redis_port}/{redis_db}')

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [redis_url],
        },
    },
}

# Production settings
if ENVIRONMENT == 'production':
    # Allow CORS from production domains - support multiple domains
    frontend_url = os.getenv('FRONTEND_URL', 'https://bingo-app.example.com')
    # Split multiple URLs if provided
    if ',' in frontend_url:
        for domain in frontend_url.split(','):
            domain = domain.strip()
            if domain and domain not in CORS_ALLOWED_ORIGINS:
                CORS_ALLOWED_ORIGINS.append(domain)
    elif frontend_url and frontend_url not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(frontend_url)
    
    # Explicitly add Vercel frontend URL if not already added
    if "https://bingo-frontend-three.vercel.app" not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append("https://bingo-frontend-three.vercel.app")
    
    # Also add CSRF trusted origins for the same domains
    CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()
    
    # Additional CORS headers for production
    CORS_ALLOW_METHODS = [
        'DELETE',
        'GET',
        'OPTIONS',
        'PATCH',
        'POST',
        'PUT',
    ]
    
    CORS_ALLOW_HEADERS = [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
    ]

# Update for Render.com deployment
# Use lowercase 'true' to match what Render.com sets
if os.getenv('RENDER', '').lower() == 'true':
    # Debug options - remove in final production
    print(f"Running on Render.com with CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")
    
    # Don't use this in production - only temporarily for debugging:
    CORS_ALLOW_ALL_ORIGINS = True
    
    # Update database configuration
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL', ''),
            conn_max_age=600
        )
    }
    
    # Security settings for Render
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Add Render URL to allowed hosts
    render_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME', '')
    if render_hostname:
        ALLOWED_HOSTS.append(render_hostname)
        render_url = f"https://{render_hostname}"
        if render_url not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(render_url.rstrip('/'))
            CSRF_TRUSTED_ORIGINS.append(render_url.rstrip('/'))
    
    # Ensure API and frontend URLs are in CSRF trusted origins
    important_urls = [
        "https://bingo-api-94i2.onrender.com",
        "https://bingo-frontend-three.vercel.app",
        # Add any new URLs here
    ]
    
    for url in important_urls:
        url = url.rstrip('/')  # Remove trailing slash
        if url not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(url)
        if url not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(url)
    
    # Configure Redis for Render
    REDIS_URL = os.getenv('REDIS_URL', '')
    if REDIS_URL:
        CHANNEL_LAYERS = {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    "hosts": [REDIS_URL],
                },
            },
        }
    
    print(f"Final CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")
    print(f"Final CSRF_TRUSTED_ORIGINS: {CSRF_TRUSTED_ORIGINS}")
