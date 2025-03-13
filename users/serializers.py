from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
import random
import string

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_email_verified')
        read_only_fields = ('is_email_verified',)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        ref_name = 'CustomRegisterSerializer'
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
    
    def create(self, validated_data):
        # Generate a 6-digit verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            verification_code=verification_code,
            verification_code_created_at=timezone.now(),
            # Auto-verify email if bypass is enabled
            is_email_verified=settings.BYPASS_EMAIL_VERIFICATION
        )
        
        # Only send verification email if bypass is not enabled
        if not settings.BYPASS_EMAIL_VERIFICATION:
            self._send_verification_email(user, verification_code)
        
        return user
    
    def _send_verification_email(self, user, code):
        subject = 'Verify your email address'
        message = f'Your verification code is: {code}'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.email]
        
        send_mail(subject, message, from_email, recipient_list)

class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    verification_code = serializers.CharField(max_length=6)
    
    def validate(self, data):
        try:
            user = User.objects.get(email=data['email'], verification_code=data['verification_code'])
            
            # Check if the code is expired (24 hours)
            if user.verification_code_created_at:
                expiration_time = user.verification_code_created_at + timezone.timedelta(hours=24)
                if timezone.now() > expiration_time:
                    raise serializers.ValidationError("Verification code has expired")
            
            return data
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or verification code")
        
    class Meta:
        ref_name = 'CustomVerifyEmailSerializer'

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email doesn't exist")
        
    class Meta:
        ref_name = 'CustomResendVerificationSerializer'