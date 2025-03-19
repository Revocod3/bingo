from django.core.management.base import BaseCommand
from django.core import management
from django.db import connection
import time

class Command(BaseCommand):
    help = 'Forces migrations by recreating tables if necessary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-reset',
            action='store_true',
            help='Force database reset (DANGEROUS: loses all data)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting force migration process...'))
        
        # First check existing tables
        self.stdout.write('Checking existing tables...')
        existing_tables = []
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
            self.stdout.write(f"Found {len(existing_tables)} existing tables:")
            for table in existing_tables:
                self.stdout.write(f"  - {table}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error checking tables: {e}"))
        
        # Check if users_customuser exists
        users_table_exists = 'users_customuser' in existing_tables
        self.stdout.write(f"users_customuser table exists: {users_table_exists}")
        
        # Check if migrations have been attempted
        migrations_table_exists = 'django_migrations' in existing_tables
        self.stdout.write(f"django_migrations table exists: {migrations_table_exists}")
        
        if options['force_reset']:
            self.stdout.write(self.style.WARNING('DANGER: Forcing database reset...'))
            management.call_command('reset_db', '--noinput', '--close-sessions')
            time.sleep(2)  # Give the database time to reset
        
        # Run migrations
        self.stdout.write(self.style.WARNING('Running migrations...'))
        management.call_command('migrate', '--noinput', '--verbosity=2')
        
        # Verify tables were created
        self.stdout.write('Verifying tables...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                user_count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"users_customuser table exists with {user_count} records"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error verifying users_customuser table: {e}"))
        
        self.stdout.write(self.style.SUCCESS('Force migration process completed'))
