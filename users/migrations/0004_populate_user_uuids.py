from django.db import migrations
import uuid


def generate_uuids(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    # Only update users with null uuid
    for user in CustomUser.objects.filter(uuid__isnull=True):
        user.uuid = uuid.uuid4()
        user.save(update_fields=['uuid'])


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_add_user_uuid'),
    ]

    operations = [
        migrations.RunPython(generate_uuids, reverse_code=migrations.RunPython.noop),
    ]
