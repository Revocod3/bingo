from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_create_superuser'),
    ]

    operations = [
        # This is just a confirmation for Django that the field exists
        # The actual column already exists in the database
        migrations.SeparateDatabaseAndState(
            # No database operation needed since column exists
            database_operations=[],
            # Just update Django's state to include the field
            state_operations=[
                migrations.AddField(
                    model_name='customuser',
                    name='uuid',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
                ),
            ]
        ),
    ]
