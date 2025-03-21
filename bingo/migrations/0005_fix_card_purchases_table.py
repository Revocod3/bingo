from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('bingo', '0004_create_missing_tables'),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE TABLE IF NOT EXISTS card_purchases (
                id SERIAL PRIMARY KEY,
                cards_owned INTEGER NOT NULL,
                purchase_date TIMESTAMP WITH TIME ZONE NOT NULL,
                last_modified TIMESTAMP WITH TIME ZONE NOT NULL,
                event_id UUID REFERENCES bingo_event(id),
                user_id INTEGER REFERENCES users_customuser(id)
            );
            
            CREATE INDEX IF NOT EXISTS card_purchases_user_id_event_id_idx ON card_purchases (user_id, event_id);
            """,
            """
            DROP TABLE IF EXISTS card_purchases;
            """
        ),
    ]
