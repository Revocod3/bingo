from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
import sys
import os
import logging
import traceback

class Command(BaseCommand):
    help = 'Checks database connection and environment configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Increase output verbosity',
        )
        parser.add_argument(
            '--exit-on-error',
            action='store_true',
            help='Exit with error code on failure',
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        exit_on_error = options['exit_on_error']
        
        # Check environment variables first
        self.stdout.write('Checking environment variables...')
        required_vars = [
            'DJANGO_SETTINGS_MODULE', 'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.environ.get(var)
            if value:
                if verbose:
                    if var != 'AWS_DB_PASSWORD':
                        self.stdout.write(f"{var}: {value}")
                    else:
                        self.stdout.write(f"{var}: ******")
            else:
                missing_vars.append(var)
                self.stderr.write(self.style.ERROR(f"{var} not set!"))
        
        if missing_vars:
            self.stderr.write(self.style.ERROR(
                f'Missing required environment variables: {", ".join(missing_vars)}'
            ))
            if exit_on_error:
                sys.exit(1)
        
        # Check database connection with better error handling
        self.stdout.write('Checking database connection...')
        try:
            db_conn = connections['default']
            db_conn.cursor()
            self.stdout.write(self.style.SUCCESS('Database connection successful!'))
            
            if verbose:
                # Print database settings (without passwords)
                try:
                    from django.conf import settings
                    db_settings = settings.DATABASES['default'].copy()
                    if 'PASSWORD' in db_settings:
                        db_settings['PASSWORD'] = '******'
                    self.stdout.write(f"Database settings: {db_settings}")
                except Exception as e:
                    self.stderr.write(self.style.WARNING(f"Could not display database settings: {e}"))
        except OperationalError as e:
            self.stderr.write(self.style.ERROR(f'Database connection failed! Error: {e}'))
            if exit_on_error:
                sys.exit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Unexpected error when connecting to database: {e}'))
            if verbose:
                self.stderr.write(traceback.format_exc())
            if exit_on_error:
                sys.exit(1)
        
        # Check if models can be used, with better error handling
        self.stdout.write('Checking models...')
        try:
            from bingo.models import Number, Event, BingoCard
            
            try:
                event_count = Event.objects.count()
                card_count = BingoCard.objects.count()
                number_count = Number.objects.count()
                
                self.stdout.write(self.style.SUCCESS(
                    f'Models check successful! Found {event_count} events, '
                    f'{card_count} bingo cards, and {number_count} numbers.'
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error querying models: {e}'))
                if verbose:
                    self.stderr.write(traceback.format_exc())
                if exit_on_error:
                    sys.exit(1)
                    
        except ImportError as e:
            self.stderr.write(self.style.ERROR(f'Error importing models: {e}'))
            if exit_on_error:
                sys.exit(1)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Unexpected error when checking models: {e}'))
            if verbose:
                self.stderr.write(traceback.format_exc())
            if exit_on_error:
                sys.exit(1)
