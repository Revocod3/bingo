"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin
from django.views.generic import TemplateView
from django.http import FileResponse
from rest_framework.routers import DefaultRouter
from users.views import (
    GoogleLoginAPIView, UserViewSet, RegisterView, VerifyEmailView, ResendVerificationView,
    FacebookLogin, GoogleLogin,
)
from users.admin_commands import run_management_command
from bingo.views import (
    DepositRequestViewSet, EventViewSet, BingoCardViewSet, NumberViewSet,
    TestCoinBalanceViewSet, CardPurchaseViewSet, WinningPatternViewSet,
    PaymentMethodViewSet, RatesConfigViewSet
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
import os
from pathlib import Path
from django.http import JsonResponse
import yaml
import json

# Import for API documentation
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Import for health check
from bingo.health import health_check
from bingo.debug import debug_info

# Create a custom view to serve the static schema file


def static_schema_view(request):
    # Path to your static schema file
    schema_path = Path(__file__).resolve().parent.parent / 'api_schema.yaml'

    try:
        # Load the YAML file
        with open(schema_path, 'r') as file:
            schema_data = yaml.safe_load(file)

        # Convert to JSON and return as JSON response
        return JsonResponse(schema_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'events', EventViewSet)
router.register(r'cards', BingoCardViewSet)
router.register(r'numbers', NumberViewSet)
router.register(r'test-coins', TestCoinBalanceViewSet)
router.register(r'card-purchases', CardPurchaseViewSet)
router.register(r'winning-patterns', WinningPatternViewSet)
router.register(r'deposits', DepositRequestViewSet, basename='deposits')
router.register(r'test-coins/deposit', DepositRequestViewSet,
                basename='deposit-request')
router.register(r'payment-methods', PaymentMethodViewSet,
                basename='payment-methods')
router.register(r'rates', RatesConfigViewSet, basename='rates')


auth_urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Custom authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationView.as_view(),
         name='resend_verification'),

    # Social auth endpoints
    path('facebook/', FacebookLogin.as_view(), name='facebook_login'),
    path('google/', GoogleLogin.as_view(), name='google_login'),

    # Custom Google login endpoint for frontend
    path('google-login/', GoogleLoginAPIView.as_view(), name='google_login_api'),

    # dj-rest-auth URLs for login, logout, password reset, etc.
    path('', include('dj_rest_auth.urls')),

    # Social auth URLs
    path('social/', include('dj_rest_auth.registration.urls')),
    path('social/facebook/', include('allauth.socialaccount.providers.facebook.urls')),
    path('social/google/', include('allauth.socialaccount.providers.google.urls')),
]

urlpatterns = [
    path('admin/run-command/', run_management_command,
         name='run_management_command'),
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include(auth_urlpatterns)),
    path('health/', health_check, name='health_check'),
    path('debug-info/', debug_info, name='debug_info'),

    # API Documentation URLs with static schema instead of dynamic generation
    path('api/schema/', static_schema_view, name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
