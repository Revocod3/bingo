from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('bingo', '0008_event_allowed_patterns'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_live',
            field=models.BooleanField(default=False),
        ),
    ]
