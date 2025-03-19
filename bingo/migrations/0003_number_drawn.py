# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0002_testcoinbalance_cardpurchase'),
    ]

    operations = [
        migrations.AddField(
            model_name='number',
            name='drawn',
            field=models.BooleanField(default=True),
        ),
    ]
