from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import sys
import os
import logging

class Command(BaseCommand):
    help = 'Checks database connection and environment configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Increase output verbosity',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        # Check database connection
        self.stdout.write('Checking database connection...')
        db_conn = connections['default']
        try:
            db_conn.cursor()
            self.stdout.write(self.style.SUCCESS('Database connection successful!'))
            
            if verbose:
                # Print database settings (without passwords)
                from django.conf import settings
                db_settings = settings.DATABASES['default'].copy()
                if 'PASSWORD' in db_settings:
                    db_settings['PASSWORD'] = '******'
                self.stdout.write(f"Database settings: {db_settings}")
        except OperationalError as e:
            self.stderr.write(self.style.ERROR(f'Database connection failed! Error: {e}'))
            self.stderr.write('\nChecking environment variables...')
            
            required_vars = [
                'AWS_DB_NAME', 'AWS_DB_USER', 'AWS_DB_HOST', 
                'AWS_DB_PORT', 'AWS_DB_SSL_MODE'
            ]
            
            for var in required_vars:
                value = os.environ.get(var)
                if value:
                    if var != 'AWS_DB_PASSWORD':
                        self.stderr.write(f"{var}: {value}")
                    else:
                        self.stderr.write(f"{var}: ******")
                else:
                    self.stderr.write(self.style.ERROR(f"{var} not set!"))
            
            sys.exit(1)
        
        # Check if Number model can be used
        self.stdout.write('Checking models...')
        try:
            from bingo.models import Number, Event, BingoCard
            event_count = Event.objects.count()
            card_count = BingoCard.objects.count()
            number_count = Number.objects.count()
            
            self.stdout.write(self.style.SUCCESS(
                f'Models check successful! Found {event_count} events, '
                f'{card_count} bingo cards, and {number_count} numbers.'
            ))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Models check failed! Error: {e}'))
            sys.exit(1)
