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
from django.urls import path, include, re_path
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from users.views import (
    UserViewSet, RegisterView, VerifyEmailView, ResendVerificationView,
    FacebookLogin, GoogleLogin
)
from bingo.views import EventViewSet, BingoCardViewSet, NumberViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import for API documentation
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'events', EventViewSet)
router.register(r'cards', BingoCardViewSet)
router.register(r'numbers', NumberViewSet)

# API Documentation schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Bingo API",
        default_version='v1',
        description="API documentation for the Bingo application",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

auth_urlpatterns = [
    # JWT Authentication
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Custom authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # Social auth endpoints
    path('facebook/', FacebookLogin.as_view(), name='facebook_login'),
    path('google/', GoogleLogin.as_view(), name='google_login'),
    
    # dj-rest-auth URLs for login, logout, password reset, etc.
    path('', include('dj_rest_auth.urls')),
    
    # Social auth URLs
    path('social/', include('dj_rest_auth.registration.urls')),
    path('social/facebook/', include('allauth.socialaccount.providers.facebook.urls')),
    path('social/google/', include('allauth.socialaccount.providers.google.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/auth/', include(auth_urlpatterns)),
    
    # API Documentation URLs with exception handling
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', 
         schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', 
         schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
    
]