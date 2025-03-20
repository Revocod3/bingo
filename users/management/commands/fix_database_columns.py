from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Fixes missing columns in database tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Check issues without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: No changes will be made'))
        
        self.stdout.write(self.style.NOTICE('Checking for missing database columns...'))
        
        issues_fixed = False
        
        # Check bingo_event.end column
        self.stdout.write('\nChecking bingo_event.end column...')
        if self._check_column_exists('bingo_event', 'end'):
            self.stdout.write(self.style.SUCCESS('  ✓ bingo_event.end column exists'))
        else:
            self.stdout.write(self.style.ERROR('  ✗ bingo_event.end column is MISSING'))
            if not dry_run:
                self._add_end_column_to_event()
                issues_fixed = True
            else:
                self.stdout.write(self.style.WARNING('  Would add end column to bingo_event table'))
            
        # Check bingo_bingocard.created_at column
        self.stdout.write('\nChecking bingo_bingocard.created_at column...')
        if self._check_column_exists('bingo_bingocard', 'created_at'):
            self.stdout.write(self.style.SUCCESS('  ✓ bingo_bingocard.created_at column exists'))
        else:
            self.stdout.write(self.style.ERROR('  ✗ bingo_bingocard.created_at column is MISSING'))
            if not dry_run:
                self._add_created_at_column_to_bingocard()
                issues_fixed = True
            else:
                self.stdout.write(self.style.WARNING('  Would add created_at column to bingo_bingocard table'))
        
        # Summary
        self.stdout.write('\nSummary:')
        if issues_fixed:
            self.stdout.write(self.style.SUCCESS('Fixed database column issues'))
        elif dry_run:
            self.stdout.write(self.style.WARNING('Issues found but not fixed (dry run)'))
        else:
            self.stdout.write(self.style.SUCCESS('No issues needed fixing'))
        
        # Verification
        if issues_fixed:
            self.stdout.write('\nVerifying fixes:')
            success = True
            
            if not self._check_column_exists('bingo_event', 'end'):
                self.stdout.write(self.style.ERROR('Failed to add bingo_event.end column'))
                success = False
            
            if not self._check_column_exists('bingo_bingocard', 'created_at'):
                self.stdout.write(self.style.ERROR('Failed to add bingo_bingocard.created_at column'))
                success = False
                
            if success:
                self.stdout.write(self.style.SUCCESS('All fixes verified successfully!'))

    def _check_column_exists(self, table_name, column_name):
        """Check if a column exists in a table"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    AND table_name = %s
                    AND column_name = %s
                );
            """, [table_name, column_name])
            return cursor.fetchone()[0]
    
    def _add_end_column_to_event(self):
        """Add missing end column to bingo_event table"""
        self.stdout.write('  Adding end column to bingo_event table...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE bingo_event 
                    ADD COLUMN "end" timestamp with time zone NOT NULL DEFAULT now();
                """)
                # Remove default constraint after adding with default
                cursor.execute("""
                    ALTER TABLE bingo_event 
                    ALTER COLUMN "end" DROP DEFAULT;
                """)
            self.stdout.write(self.style.SUCCESS('  Successfully added end column to bingo_event table'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Failed to add end column: {str(e)}'))
    
    def _add_created_at_column_to_bingocard(self):
        """Add missing created_at column to bingo_bingocard table"""
        self.stdout.write('  Adding created_at column to bingo_bingocard table...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    ALTER TABLE bingo_bingocard 
                    ADD COLUMN created_at timestamp with time zone NOT NULL DEFAULT now();
                """)
                # Remove default constraint after adding with default
                cursor.execute("""
                    ALTER TABLE bingo_bingocard 
                    ALTER COLUMN created_at DROP DEFAULT;
                """)
            self.stdout.write(self.style.SUCCESS('  Successfully added created_at column to bingo_bingocard table'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Failed to add created_at column: {str(e)}'))
