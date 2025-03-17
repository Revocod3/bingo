from django.core.management.base import BaseCommand
from django.db import connections
from django.conf import settings
import socket
import sys
import os
import time
import subprocess

class Command(BaseCommand):
    help = 'Check database connection and configuration'

    def handle(self, *args, **options):
        # Print environment info
        self.stdout.write(self.style.NOTICE("Environment Information:"))
        self.stdout.write(f"ENVIRONMENT: {os.getenv('ENVIRONMENT', 'local')}")
        self.stdout.write(f"DATABASE_URL defined: {'Yes' if os.getenv('DATABASE_URL') else 'No'}")
        
        # Print database config (with password masked)
        self.stdout.write(self.style.NOTICE("\nDatabase Configuration:"))
        db_config = settings.DATABASES['default'].copy()
        if 'PASSWORD' in db_config:
            db_config['PASSWORD'] = '********' if db_config['PASSWORD'] else '(none)'
        self.stdout.write(str(db_config))
        
        # Test hostname resolution
        host = settings.DATABASES['default'].get('HOST')
        self.stdout.write(self.style.NOTICE(f"\nTesting hostname resolution for: {host}"))
        try:
            ip_address = socket.gethostbyname(host)
            self.stdout.write(self.style.SUCCESS(f"✓ Hostname resolves to: {ip_address}"))
            
            # Check if we're on Render.com and running a traceroute/ping
            if os.getenv('ENVIRONMENT') == 'render':
                self.stdout.write(self.style.NOTICE(f"\nTesting network connectivity to {host}:"))
                try:
                    result = subprocess.run(['ping', '-c', '3', host], 
                                           capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        self.stdout.write(self.style.SUCCESS("✓ Host is reachable via ping"))
                    else:
                        self.stdout.write(self.style.ERROR(f"✗ Host ping failed: {result.stderr}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Couldn't run ping test: {str(e)}"))
        except socket.gaierror as e:
            self.stdout.write(self.style.ERROR(f"✗ Hostname resolution failed: {str(e)}"))
            
            # More detailed suggestions for Render deployment
            if os.getenv('ENVIRONMENT') == 'render':
                self.stdout.write(self.style.WARNING(
                    "\nOn Render.com, hostname resolution failures are often due to:"
                ))
                self.stdout.write("1. Incorrect database URL format")
                self.stdout.write("2. Missing domain suffix in the hostname")
                self.stdout.write("3. Network configuration issues in the Render environment")
                
                # Check if DATABASE_URL is present and well-formed
                db_url = os.getenv('DATABASE_URL', '')
                if db_url:
                    self.stdout.write(self.style.NOTICE("\nChecking DATABASE_URL format:"))
                    if db_url.startswith('postgres://') or db_url.startswith('postgresql://'):
                        self.stdout.write(self.style.SUCCESS("✓ DATABASE_URL has correct protocol prefix"))
                    else:
                        self.stdout.write(self.style.ERROR("✗ DATABASE_URL has incorrect protocol prefix"))
                    
                    # Basic URL format check
                    url_parts = db_url.split('@')
                    if len(url_parts) == 2 and len(url_parts[1].split('/')) >= 1:
                        host_part = url_parts[1].split('/')[0]
                        self.stdout.write(f"  Host part in URL: {host_part}")
                        if '.' in host_part:
                            self.stdout.write(self.style.SUCCESS("✓ Host part contains domain suffix"))
                        else:
                            self.stdout.write(self.style.ERROR("✗ Host part is missing domain suffix"))
            elif '.' not in host:
                self.stdout.write(self.style.WARNING(
                    "The hostname appears to be incomplete. "
                    "Make sure you're using the fully qualified domain name."
                ))
        
        # Test database connection
        self.stdout.write(self.style.NOTICE("\nTesting database connection:"))
        conn = connections['default']
        start_time = time.time()
        try:
            conn.ensure_connection()
            duration = time.time() - start_time
            self.stdout.write(self.style.SUCCESS(f"✓ Connected successfully in {duration:.2f} seconds"))
            
            # Get some basic info from the database
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(f"Database version: {version}")
                
                cursor.execute("SELECT current_database();")
                db_name = cursor.fetchone()[0]
                self.stdout.write(f"Connected to database: {db_name}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Connection failed: {str(e)}"))
            self.stdout.write(self.style.WARNING("\nPossible solutions:"))
            self.stdout.write("1. Check if the database server is running")
            self.stdout.write("2. Verify credentials and hostname are correct")
            self.stdout.write("3. Check network connectivity and firewall settings")
            
            if os.getenv('ENVIRONMENT') == 'render':
                self.stdout.write("4. Check if the Render database service is active")
                self.stdout.write("5. Verify the database URL is correctly set in the Render dashboard")
                self.stdout.write("6. Try redeploying the application")
            else:
                self.stdout.write(f"4. Set ENVIRONMENT=render if you're running on Render.com")
