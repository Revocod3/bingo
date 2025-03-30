from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import exceptions
from users.serializers import UserSerializer

User = get_user_model()

class EmailVerificationBackend(ModelBackend):
    """
    Authentication backend that verifies if the user's email is verified
    before allowing them to login.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First authenticate using the parent class method
        user = super().authenticate(request, username, password, **kwargs)
        
        # If authentication succeeded, check if email is verified
        if user and not user.is_email_verified and not user.is_superuser:
            # Return None to indicate authentication failed
            return None
            
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that checks if the user's email is verified
    and includes user data in the response.
    """
    def validate(self, attrs):
        # Check if user exists and get user object
        user = User.objects.filter(email=attrs['email']).first()
        
        # Check if user exists and has verified email
        if user and not user.is_email_verified and not user.is_superuser:
            raise exceptions.AuthenticationFailed(
                'Email not verified. Please check your inbox for the verification email or request a new one.'
            )
            
        # Call parent validate method to get tokens
        data = super().validate(attrs)
        
        # Add user data to response
        user = self.user
        user_serializer = UserSerializer(user)
        data['user'] = user_serializer.data
        
        return data
