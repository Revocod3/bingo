from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
import random
import string
import logging
from users.serializers import RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test user registration and email verification flow'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='Email address for the test user')
        parser.add_argument('--password', type=str, default='testpassword123', help='Password for the test user')
        parser.add_argument('--first_name', type=str, default='Test', help='First name for the test user')
        parser.add_argument('--last_name', type=str, default='User', help='Last name for the test user')

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']
        
        # First check if user exists and delete them for testing
        try:
            existing_user = User.objects.get(email=email)
            self.stdout.write(self.style.WARNING(f'Found existing user with email {email}, deleting for test...'))
            existing_user.delete()
        except User.DoesNotExist:
            pass
            
        # Create test data for registration
        user_data = {
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name
        }
        
        self.stdout.write(self.style.NOTICE("Starting user registration test..."))
        self.stdout.write(f"Email backend: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"BYPASS_EMAIL_VERIFICATION: {settings.BYPASS_EMAIL_VERIFICATION}")
        
        # Use the RegisterSerializer to simulate the registration API
        serializer = RegisterSerializer(data=user_data)
        
        if serializer.is_valid():
            try:
                # Create the user
                user = serializer.save()
                self.stdout.write(self.style.SUCCESS(f"✓ User created successfully with email: {email}"))
                
                # Display verification code (only in development)
                if user.verification_code:
                    self.stdout.write(self.style.SUCCESS(f"✓ Verification code generated: {user.verification_code}"))
                    
                # Check verification status
                if user.is_email_verified:
                    self.stdout.write(self.style.SUCCESS("✓ Email automatically verified (bypass enabled)"))
                else:
                    self.stdout.write(self.style.NOTICE(
                        "i Email needs verification. Check your console output for the email content."
                    ))
                    self.stdout.write(self.style.NOTICE(
                        "i If using console backend, the email content should appear in your server logs."
                    ))
                    
                # Provide instructions for verification
                self.stdout.write("\nTo test email verification, use:")
                self.stdout.write(f"  python manage.py verify_email --email={email} --code={user.verification_code}")
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Registration failed: {str(e)}"))
                logger.error(f"Registration test failed: {str(e)}")
        else:
            self.stdout.write(self.style.ERROR("✗ Invalid registration data:"))
            for field, errors in serializer.errors.items():
                self.stdout.write(f"  - {field}: {', '.join(errors)}")
