from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email sending functionality'

    def handle(self, *args, **options):
        try:
            send_mail(
                'Test Email from Bingo App',
                'This is a test email from your Bingo application.',
                settings.DEFAULT_FROM_EMAIL,
                [options.get('email', 'test@example.com')],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('Test email sent successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {str(e)}'))
            logger.error(f"Email sending failed: {str(e)}")

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test to')
