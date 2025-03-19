from django.db import migrations

class Migration(migrations.Migration):
    """
    This migration ensures that all tables are properly created.
    """
    dependencies = [
        ('bingo', '0002_fix_duplicate_table'),
    ]

    operations = []
