from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('bingo', '0007_default_winning_patterns'),  # Asegúrate que esta sea la última migración existente
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='disabled_patterns',
            field=models.ManyToManyField(blank=True, related_name='disabled_in_events', to='bingo.winningpattern'),
        ),
    ]
