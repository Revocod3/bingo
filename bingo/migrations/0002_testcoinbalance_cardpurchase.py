# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bingo', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestCoinBalance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('balance', models.PositiveIntegerField(default=100)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='test_coins', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'test_coin_balance',
            },
        ),
        migrations.CreateModel(
            name='CardPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cards_owned', models.PositiveIntegerField(default=0)),
                ('purchase_date', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card_purchases', to='bingo.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card_purchases', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'card_purchases',
                'unique_together': {('user', 'event')},
            },
        ),
        migrations.AddIndex(
            model_name='testcoinbalance',
            index=models.Index(fields=['user'], name='test_coin_b_user_id_c4140f_idx'),
        ),
        migrations.AddIndex(
            model_name='cardpurchase',
            index=models.Index(fields=['user', 'event'], name='card_purcha_user_id_21d58c_idx'),
        ),
    ]
