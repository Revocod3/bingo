from django.shortcuts import render
from rest_framework import viewsets, status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from django.contrib.auth import get_user_model
from django.utils import timezone
import random
import string
from django.conf import settings
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    VerifyEmailSerializer,
    ResendVerificationSerializer
)
from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView

User = get_user_model()

class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter
    callback_url = 'http://localhost:3000/auth/facebook/callback/'  # Frontend callback URL
    client_class = OAuth2Client

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:3000/auth/google/callback/'  # Frontend callback URL
    client_class = OAuth2Client

class UserViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing user instances.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Get the current authenticated user's profile
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class RegisterView(generics.CreateAPIView):
    """
    Register a new user with email and password
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class VerifyEmailView(generics.GenericAPIView):
    """
    Verify email with the provided verification code
    """
    serializer_class = VerifyEmailSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Mark email as verified
        user.is_email_verified = True
        user.verification_code = None
        user.verification_code_created_at = None
        user.save()
        
        return Response({"detail": "Email verified successfully"}, status=status.HTTP_200_OK)

class ResendVerificationView(generics.GenericAPIView):
    """
    Resend email verification code
    """
    serializer_class = ResendVerificationSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Auto-verify if bypass is enabled
        if settings.BYPASS_EMAIL_VERIFICATION:
            user.is_email_verified = True
            user.verification_code = None
            user.verification_code_created_at = None
            user.save()
            return Response({"detail": "Email verified automatically for development"}, status=status.HTTP_200_OK)
        
        # Generate new verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        user.verification_code = verification_code
        user.verification_code_created_at = timezone.now()
        user.save()
        
        # Send verification email
        from django.core.mail import send_mail
        
        subject = 'Verify your email address'
        message = f'Your verification code is: {verification_code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        send_mail(subject, message, from_email, recipient_list)
        
        return Response({"detail": "Verification code sent"}, status=status.HTTP_200_OK)