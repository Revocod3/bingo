from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('bingo', '0007_default_winning_patterns'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='allowed_patterns',
            field=models.ManyToManyField(blank=True, related_name='events', to='bingo.winningpattern'),
        ),
    ]
