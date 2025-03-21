from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check database schema for users_customuser table'

    def handle(self, *args, **options):
        self.stdout.write("Checking database schema...")
        
        with connection.cursor() as cursor:
            # Check if the column exists
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users_customuser'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            self.stdout.write("\nTable structure for users_customuser:")
            for col in columns:
                self.stdout.write(f"  - Column: {col[0]}, Type: {col[1]}, Nullable: {col[2]}")
            
            # Check model definition
            self.stdout.write("\nChecking CustomUser model definition...")
            from users.models import CustomUser
            for field in CustomUser._meta.get_fields():
                self.stdout.write(f"  - Field: {field.name}, Type: {field.__class__.__name__}")
            
            # Check database constraints
            cursor.execute("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conrelid = 'users_customuser'::regclass::oid;
            """)
            constraints = cursor.fetchall()
            
            self.stdout.write("\nConstraints on users_customuser:")
            for con in constraints:
                con_type = {
                    'p': 'PRIMARY KEY',
                    'u': 'UNIQUE',
                    'f': 'FOREIGN KEY',
                    'c': 'CHECK'
                }.get(con[1], con[1])
                self.stdout.write(f"  - {con[0]}: {con_type}")
        
        self.stdout.write(self.style.SUCCESS("Schema check complete"))
