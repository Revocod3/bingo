# Generated by Django 5.1.7 on 2025-04-01 23:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0004_paymentmethod'),
    ]

    operations = [
        migrations.CreateModel(
            name='RatesConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rates', models.JSONField(default=dict)),
                ('description', models.CharField(blank=True, max_length=255, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuración de Tasas',
                'verbose_name_plural': 'Configuración de Tasas',
            },
        ),
    ]
