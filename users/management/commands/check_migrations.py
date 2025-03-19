from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps
import os
import sys
import logging

class Command(BaseCommand):
    help = 'Checks and diagnoses migration issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Checking migration status...'))
        
        # Check django_migrations table exists
        self.stdout.write('Checking if migration table exists...')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' 
                    AND tablename = 'django_migrations'
                );
            """)
            migration_table_exists = cursor.fetchone()[0]
            
            if not migration_table_exists:
                self.stdout.write(self.style.ERROR('django_migrations table does not exist!'))
                self.stdout.write(self.style.NOTICE('This indicates migrations have not been run at all.'))
                return
            else:
                self.stdout.write(self.style.SUCCESS('django_migrations table exists.'))
        
        # Check which migrations have been applied
        self.stdout.write('Checking applied migrations...')
        with connection.cursor() as cursor:
            cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name;")
            applied_migrations = cursor.fetchall()
            
        if not applied_migrations:
            self.stdout.write(self.style.WARNING('No migrations have been applied yet.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Found {len(applied_migrations)} applied migrations:'))
            for app, name in applied_migrations:
                self.stdout.write(f'  - {app}: {name}')
                
        # Check for users_customuser table specifically
        self.stdout.write('\nChecking for users_customuser table...')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                   SELECT FROM information_schema.tables 
                   WHERE table_schema = 'public'
                   AND table_name = 'users_customuser'
                );
            """)
            users_table_exists = cursor.fetchone()[0]
            
        if users_table_exists:
            self.stdout.write(self.style.SUCCESS('users_customuser table exists.'))
        else:
            self.stdout.write(self.style.ERROR('users_customuser table DOES NOT exist!'))
            self.stdout.write(self.style.NOTICE('This indicates the users migrations have not been applied properly.'))
            
            # Check if users is in INSTALLED_APPS
            from django.conf import settings
            if 'users' not in settings.INSTALLED_APPS:
                self.stdout.write(self.style.ERROR("'users' is not in INSTALLED_APPS!"))
            else:
                self.stdout.write(self.style.SUCCESS("'users' is in INSTALLED_APPS."))
            
            # List tables that do exist
            self.stdout.write('\nListing existing tables:')
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY tablename;
            """)
            tables = cursor.fetchall()
            for table in tables:
                self.stdout.write(f'  - {table[0]}')
                
        # Suggest solutions
        self.stdout.write('\nPossible solutions:')
        self.stdout.write('1. Run migrations: python manage.py migrate')
        self.stdout.write('2. Check database connection settings')
        self.stdout.write('3. Ensure users app is in INSTALLED_APPS')
        self.stdout.write('4. Check for migration conflicts')
