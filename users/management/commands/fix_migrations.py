from django.core.management.base import BaseCommand
from django.db import connection
from django.core import management

class Command(BaseCommand):
    help = 'Fix common migration issues by ensuring tables match model definitions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check for issues without fixing',
        )

    def handle(self, *args, **options):
        check_only = options['check_only']
        self.stdout.write(self.style.NOTICE('Checking for migration issues...'))
        
        # First run the diagnostic command
        self.stdout.write('\nRunning migration diagnostics:')
        management.call_command('check_migrations')
        
        # Then fix specific column issues
        self.stdout.write('\nFixing specific column issues:')
        if check_only:
            management.call_command('fix_database_columns', '--dry-run')
        else:
            management.call_command('fix_database_columns')
            
            # Also run migrations to make sure everything is up to date
            self.stdout.write('\nRunning migrations to ensure all tables are up to date:')
            management.call_command('migrate', '--no-input')
            
            self.stdout.write(self.style.SUCCESS('\nMigration issues should now be fixed!'))
            self.stdout.write(self.style.NOTICE('Please restart your Django application'))
