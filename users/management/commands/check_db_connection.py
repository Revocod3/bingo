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
            
            # Check network connectivity
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
            
            # More detailed suggestions for AWS deployment
            if os.getenv('ENVIRONMENT') == 'production':
                self.stdout.write(self.style.WARNING(
                    "\nHostname resolution failures are often due to:"
                ))
                self.stdout.write("1. Incorrect database URL format")
                self.stdout.write("2. VPC or security group configuration issues")
                self.stdout.write("3. AWS RDS endpoint might be incorrect")
                
                # Check if AWS DB environment variables are present
                aws_db_host = os.getenv('AWS_DB_HOST', '')
                if aws_db_host:
                    self.stdout.write(self.style.NOTICE("\nChecking AWS RDS hostname format:"))
                    if '.rds.amazonaws.com' in aws_db_host:
                        self.stdout.write(self.style.SUCCESS("✓ AWS RDS hostname appears to be valid"))
                    else:
                        self.stdout.write(self.style.WARNING("⚠ AWS RDS hostname doesn't contain '.rds.amazonaws.com'"))
                    
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
                
                # Check SSL connection for AWS RDS
                if os.getenv('ENVIRONMENT') == 'production':
                    cursor.execute("SHOW ssl;")
                    ssl_status = cursor.fetchone()[0]
                    if ssl_status == 'on':
                        self.stdout.write(self.style.SUCCESS("✓ SSL is enabled for this connection"))
                    else:
                        self.stdout.write(self.style.WARNING("⚠ SSL is not enabled for this connection"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Connection failed: {str(e)}"))
            self.stdout.write(self.style.WARNING("\nPossible solutions:"))
            self.stdout.write("1. Check if the database server is running")
            self.stdout.write("2. Verify credentials and hostname are correct")
            self.stdout.write("3. Check network connectivity and security groups/firewall settings")
            
            if os.getenv('ENVIRONMENT') == 'production':
                self.stdout.write("4. Check if the AWS RDS instance is active and publicly accessible")
                self.stdout.write("5. Verify security groups allow access from your application")
                self.stdout.write("6. Check if the database endpoint URL is correct")
            else:
                self.stdout.write(f"4. Set ENVIRONMENT=production if you're running in production")
