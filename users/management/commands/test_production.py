from django.core.management.base import BaseCommand
from django.core import management
from django.conf import settings
import os
import requests

class Command(BaseCommand):
    help = 'Run comprehensive tests on the production environment'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, default='test@example.com', help='Email for testing')
        parser.add_argument('--password', type=str, default='TestPassword123!', help='Password for testing')
        parser.add_argument('--skip-email', action='store_true', help='Skip email tests')
        parser.add_argument('--skip-db', action='store_true', help='Skip database tests')

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🧪 PRODUCTION ENVIRONMENT TEST 🧪"))
        self.stdout.write(self.style.NOTICE("=============================="))
        
        # Environment check
        self.stdout.write(self.style.NOTICE("\n1️⃣ Checking environment settings..."))
        env = os.getenv('ENVIRONMENT', 'local')
        self.stdout.write(f"Current environment: {env}")
        
        if env != 'production':
            self.stdout.write(self.style.WARNING("⚠️  Not running in production environment!"))
            if input("Continue anyway? (y/n): ").lower() != 'y':
                self.stdout.write("Test cancelled.")
                return
        
        # Database connection test
        if not options['skip_db']:
            self.stdout.write(self.style.NOTICE("\n2️⃣ Testing database connection..."))
            try:
                management.call_command('check_db_connection', verbosity=1)
                self.stdout.write(self.style.SUCCESS("✅ Database connection successful"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Database connection failed: {str(e)}"))
                return
        
        # Email test
        if not options['skip_email']:
            self.stdout.write(self.style.NOTICE("\n3️⃣ Testing email sending..."))
            try:
                management.call_command('test_email', email=options['email'])
                self.stdout.write(self.style.SUCCESS(f"✅ Test email sent to {options['email']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Email sending failed: {str(e)}"))
        
        # Registration test
        self.stdout.write(self.style.NOTICE("\n4️⃣ Testing user registration..."))
        try:
            management.call_command(
                'test_registration',
                email=options['email'],
                password=options['password']
            )
            self.stdout.write(self.style.SUCCESS("✅ Registration test completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Registration test failed: {str(e)}"))
        
        # API endpoints test
        self.stdout.write(self.style.NOTICE("\n5️⃣ Testing API endpoints..."))
        hostname = os.getenv('FRONTEND_URL', '').replace('https://', '').replace('http://', '').rstrip('/')
        
        if not hostname:
            self.stdout.write(self.style.WARNING("⚠️  FRONTEND_URL not set, skipping API tests"))
        else:
            api_url = f"https://{hostname}/api"
            try:
                self.stdout.write(f"Testing API at {api_url}")
                response = requests.get(f"{api_url}/health/", timeout=5)
                if response.status_code == 200:
                    self.stdout.write(self.style.SUCCESS(f"✅ API health endpoint returned {response.status_code}"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  API health endpoint returned {response.status_code}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Failed to connect to API: {str(e)}"))
        
        self.stdout.write(self.style.NOTICE("\n🏁 Production tests completed"))
