from django.db import migrations
from django.contrib.auth.hashers import make_password
import os

def create_superuser(apps, schema_editor):
    User = apps.get_model('users', 'CustomUser')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'password')
    
    if not User.objects.filter(email=email).exists():
        User.objects.create(
            email=email,
            password=make_password(password),
            first_name=os.environ.get('DJANGO_SUPERUSER_FIRST_NAME', 'Admin'),
            last_name=os.environ.get('DJANGO_SUPERUSER_LAST_NAME', 'User'),
            is_staff=True,
            is_active=True,
            is_superuser=True,
            is_email_verified=True
        )

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_superuser)
    ]
