from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging
from allauth.account.models import EmailAddress

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email verification process'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, required=True, help='User email address')
        parser.add_argument('--code', type=str, required=True, help='Verification code')

    def handle(self, *args, **options):
        email = options['email']
        code = options['code']
        
        try:
            # Find user with given email
            user = User.objects.get(email=email)
            
            # Check verification code
            if user.verification_code != code:
                self.stdout.write(self.style.ERROR("✗ Invalid verification code"))
                return
                
            # Check if code is expired (24 hours)
            if user.verification_code_created_at:
                expiration_time = user.verification_code_created_at + timezone.timedelta(hours=24)
                if timezone.now() > expiration_time:
                    self.stdout.write(self.style.ERROR("✗ Verification code has expired"))
                    return
            
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
            
            self.stdout.write(self.style.SUCCESS(f"✓ Email {email} verified successfully!"))
            self.stdout.write(self.style.SUCCESS("✓ User can now log in"))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ No user found with email {email}"))
