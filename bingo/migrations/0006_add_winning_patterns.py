from django.conf import settings
from django.db import migrations, models
import uuid

class Migration(migrations.Migration):
    dependencies = [
        ('bingo', '0005_fix_card_purchases_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='WinningPattern',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('positions', models.JSONField(help_text='JSON array of positions that form this pattern')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='created_patterns', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
