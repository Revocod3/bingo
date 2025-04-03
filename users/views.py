import logging
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
from allauth.account.models import EmailAddress
from django.db.utils import OperationalError
from rest_framework.exceptions import APIException
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import GoogleLoginSerializer

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
    
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except OperationalError as e:
            # Log the database connection error
            logging.error(f"Database connection error during registration: {str(e)}")
            # Return a service unavailable response
            raise APIException(
                "Database connection error. Please try again later."
            )

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
        
        # Also update EmailAddress record for django-allauth
        email_address, created = EmailAddress.objects.get_or_create(
            user=user, 
            email=email,
            defaults={'primary': True, 'verified': True}
        )
        if not created:
            email_address.verified = True
            email_address.save()
        
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

class GoogleLoginAPIView(APIView):
    """
    Custom view to handle Google login from frontend
    This endpoint receives a Google ID and email from the frontend
    and creates or updates a user in our system
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = GoogleLoginSerializer
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        google_id = serializer.validated_data['google_id']
        name = serializer.validated_data.get('name', '')
        
        try:
            # Check if user exists with this email
            user = User.objects.get(email=email)
            # Update user if needed (can add more fields here if necessary)
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save()
        except User.DoesNotExist:
            # Create new user
            first_name = name.split(' ')[0] if ' ' in name else name
            last_name = ' '.join(name.split(' ')[1:]) if ' ' in name else ''
            
            user = User.objects.create_user(
                email=email,
                # Generate a random secure password for the user
                password=''.join(random.choices(string.ascii_letters + string.digits, k=32)),
                first_name=first_name,
                last_name=last_name,
                is_email_verified=True
            )
            
            # Create EmailAddress record for django-allauth
            EmailAddress.objects.create(
                user=user,
                email=user.email,
                primary=True,
                verified=True
            )
        
        # Create tokens for the user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Return the token and user details
        user_serializer = UserSerializer(user)
        return Response({
            'access': access_token,
            'refresh': str(refresh),
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)