from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_populate_user_uuids'),
    ]

    operations = [
        # First check if any null values remain
        migrations.RunSQL(
            """
            UPDATE users_customuser 
            SET uuid = gen_random_uuid() 
            WHERE uuid IS NULL;
            """
        ),
        # Then make it non-null
        migrations.RunSQL(
            """
            DO $$
            BEGIN
                ALTER TABLE users_customuser ALTER COLUMN uuid SET NOT NULL;
                
                -- Check if the constraint already exists before adding it
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint 
                    WHERE conname = 'users_customuser_uuid_key' 
                    AND conrelid = 'users_customuser'::regclass::oid
                ) THEN
                    ALTER TABLE users_customuser ADD CONSTRAINT users_customuser_uuid_key UNIQUE (uuid);
                END IF;
            END $$;
            """
        ),
    ]
