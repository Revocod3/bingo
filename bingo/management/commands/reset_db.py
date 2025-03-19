import logging
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Resets the database and re-initializes it before seeding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--noinput', '--no-input', action='store_true',
            help='Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Force reset without confirmation (use with caution)',
        )

    def handle(self, *args, **options):
        if not options['force'] and not options['noinput']:
            confirm = input("""
            ⚠️  WARNING: This will DELETE ALL DATA in your database. ⚠️
            Are you sure you want to continue? (yes/no): 
            """).lower().strip()
            
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Reset operation cancelled.'))
                return
        
        self.stdout.write(self.style.WARNING('Resetting the database...'))
        
        # Get a list of app models to drop (excluding Django internals)
        with connection.cursor() as cursor:
            # Clear specific tables related to our app
            self.stdout.write('Clearing bingo cards...')
            cursor.execute("DELETE FROM bingo_bingocard;")
            
            self.stdout.write('Clearing called numbers...')
            cursor.execute("DELETE FROM bingo_number;")
            
            self.stdout.write('Clearing events...')
            cursor.execute("DELETE FROM bingo_event;")
        
        self.stdout.write(self.style.SUCCESS('Database tables cleared'))
        
        # Run migrations to ensure schema is up to date
        self.stdout.write('Running migrations...')
        call_command('migrate', interactive=False)
        
        # Now run the seed_db command
        self.stdout.write('Seeding the database...')
        call_command('seed_db')
        
        self.stdout.write(self.style.SUCCESS('Database reset and seeded successfully'))
